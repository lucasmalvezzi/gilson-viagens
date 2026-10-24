import {
  ChangeDetectionStrategy,
  Component,
  OnDestroy,
  OnInit,
  ViewEncapsulation,
  computed,
  inject,
  signal
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { FlightModalComponent } from './components/flight-modal.component';
import { ScraperLogConsoleComponent } from './components/scraper-log-console.component';
import { AeroportoInfo } from './models/airports.data';
import {
  ConfigBusca,
  HistoricoPreco,
  ScraperLogEntry,
  SearchResult,
  SystemSettings,
  WindowsSchedulerStatus
} from './models/flight.model';
import { FlightService } from './services/flight.service';
import {
  agruparHistoricoPorRota,
  buscarInfoAeroporto,
  contabilizarResumoLogs,
  criarRascunhoPadraoBusca,
  extrairMensagemErroHttp,
  obterDataFuturaIso,
  obterNomeMesPorNumero,
  validarEMontarPayloadBusca
} from './utils/flight-search-planner';

@Component({
  selector: 'app-root',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
  imports: [
    CommonModule,
    FormsModule,
    ScraperLogConsoleComponent,
    FlightModalComponent
  ],
  templateUrl: './app.html',
  styleUrls: [
    './styles/shell-and-metrics.css',
    './styles/flight-cards.css',
    './styles/history-and-settings.css',
    './styles/modal-and-autocomplete.css',
    './styles/scraper-terminal.css'
  ]
})
export class App implements OnInit, OnDestroy {
  private readonly flightService = inject(FlightService);
  private logsTimer: ReturnType<typeof setInterval> | null = null;

  readonly activeTab = signal<'buscas' | 'historico' | 'configuracoes' | 'avancado'>('buscas');
  readonly configs = signal<ConfigBusca[]>([]);
  readonly historico = signal<HistoricoPreco[]>([]);
  readonly settings = signal<SystemSettings>({
    horario_execucao: '09:00',
    telegram_bot_token: '',
    telegram_chat_id: ''
  });
  readonly windowsScheduler = signal<WindowsSchedulerStatus>({
    suportado: true,
    total_tarefas: 0,
    comando_standalone: '',
    tarefas: [],
    mensagem: ''
  });

  readonly loadingConfigs = signal(false);
  readonly loadingHistorico = signal(false);
  readonly buscandoId = signal<number | null>(null);
  readonly executandoTudo = signal(false);
  readonly testandoTelegram = signal(false);
  readonly sincronizandoWindows = signal(false);
  readonly showModalNovaBusca = signal(false);
  readonly editandoConfigId = signal<number | null>(null);
  readonly tipoData = signal<'intervalo' | 'mes'>('intervalo');
  readonly filtroBuscaHistorico = signal<number | null>(null);
  readonly toast = signal<{ mensagem: string; tipo: 'success' | 'error' | 'info' } | null>(null);

  readonly logs = signal<ScraperLogEntry[]>([]);
  readonly loadingLogs = signal(false);
  readonly autoRefreshLogs = signal<boolean>(true);
  readonly gruposRecolhidos = signal<Record<number, boolean>>({});

  readonly novaBusca = signal<Partial<ConfigBusca>>(criarRascunhoPadraoBusca());

  readonly historicoAgrupado = computed(() =>
    agruparHistoricoPorRota(this.historico(), this.configs())
  );

  readonly resumoLogs = computed(() =>
    contabilizarResumoLogs(this.logs())
  );

  /**
   * Inicializa os dados do painel e o temporizador de live-tail de logs.
   * Exemplo: executado automaticamente pelo ciclo de vida do Angular.
   */
  ngOnInit(): void {
    this.carregarConfigs();
    this.carregarHistorico();
    this.carregarSettings();
    this.carregarStatusWindowsScheduler();
    this.carregarLogs(true);
    this.iniciarPollingDeLogs();
  }

  /**
   * Cancela o temporizador de live-tail ao destruir o componente.
   * Exemplo: executado automaticamente pelo Angular.
   */
  ngOnDestroy(): void {
    if (this.logsTimer !== null) {
      clearInterval(this.logsTimer);
      this.logsTimer = null;
    }
  }

  private iniciarPollingDeLogs(): void {
    this.logsTimer = setInterval(() => {
      const naAbaAvancado = this.activeTab() === 'avancado' && this.autoRefreshLogs();
      const executandoBusca = this.buscandoId() !== null || this.executandoTudo();
      if (naAbaAvancado || executandoBusca) this.carregarLogs(true);
    }, 3000);
  }

  /**
   * Retorna o nome do mês por extenso para exibição nos cards.
   * Exemplo: `getNomeMes(11)` -> `'Novembro'`
   */
  getNomeMes(numeroMes: number | null | undefined): string {
    const nome = obterNomeMesPorNumero(numeroMes);
    return nome;
  }

  /**
   * Busca os metadados do aeroporto pelo código IATA.
   * Exemplo: `getInfoAeroporto('GRU')`
   */
  getInfoAeroporto(iata: string | undefined | null): AeroportoInfo | undefined {
    const info = buscarInfoAeroporto(iata);
    return info;
  }

  /**
   * Exibe um banner temporário de feedback (toast) no topo da tela.
   * Exemplo: `showToast('Configurações salvas!', 'success')`
   */
  showToast(mensagem: string, tipo: 'success' | 'error' | 'info' = 'info'): void {
    this.toast.set({ mensagem, tipo });
    setTimeout(() => this.toast.set(null), 4500);
  }

  /**
   * Muda para a aba Avançado e recarrega os logs imediatamente.
   * Exemplo: `abrirTabAvancado()`
   */
  abrirTabAvancado(): void {
    this.activeTab.set('avancado');
    this.carregarLogs();
  }

  /**
   * Consulta os logs mais recentes do webscraper no backend.
   * Exemplo: `carregarLogs(true)`
   */
  carregarLogs(silencioso = false): void {
    if (!silencioso) this.loadingLogs.set(true);
    this.flightService.getLogs(400).subscribe({
      next: resposta => {
        this.logs.set(resposta.logs ?? []);
        if (!silencioso) this.loadingLogs.set(false);
      },
      error: () => this.tratarErroCarregamentoLogs(silencioso)
    });
  }

  private tratarErroCarregamentoLogs(silencioso: boolean): void {
    if (silencioso) return;
    this.showToast('Erro ao carregar logs do webscraper.', 'error');
    this.loadingLogs.set(false);
  }

  /**
   * Solicita confirmação e limpa todos os logs do console.
   * Exemplo: `limparLogs()`
   */
  limparLogs(): void {
    if (!confirm('Deseja limpar todo o histórico de logs do console?')) return;
    this.flightService.clearLogs().subscribe({
      next: () => {
        this.carregarLogs();
        this.showToast('Console de logs limpo.', 'info');
      },
      error: () => this.showToast('Falha ao limpar logs.', 'error')
    });
  }

  /**
   * Carrega todos os monitoramentos de voo cadastrados.
   * Exemplo: `carregarConfigs()`
   */
  carregarConfigs(): void {
    this.loadingConfigs.set(true);
    this.flightService.getConfigs().subscribe({
      next: lista => { this.configs.set(lista ?? []); this.loadingConfigs.set(false); },
      error: () => { this.showToast('Erro ao carregar monitoramentos.', 'error'); this.loadingConfigs.set(false); }
    });
  }

  /**
   * Carrega o histórico de preços aplicando o filtro de trecho atual.
   * Exemplo: `carregarHistorico()`
   */
  carregarHistorico(): void {
    this.loadingHistorico.set(true);
    const idFiltro = this.filtroBuscaHistorico();
    this.flightService.getHistorico(idFiltro ?? undefined).subscribe({
      next: itens => { this.historico.set(itens ?? []); this.loadingHistorico.set(false); },
      error: () => { this.historico.set([]); this.showToast('Erro ao carregar histórico.', 'error'); this.loadingHistorico.set(false); }
    });
  }

  /**
   * Carrega as configurações globais do sistema (Telegram e agendamento).
   * Exemplo: `carregarSettings()`
   */
  carregarSettings(): void {
    this.flightService.getSettings().subscribe({
      next: cfgSistema => this.settings.set(cfgSistema),
      error: () => this.showToast('Erro ao carregar configurações.', 'error')
    });
  }

  /**
   * Consulta o estado atual das tarefas registradas no Agendador do Windows.
   * Exemplo: `carregarStatusWindowsScheduler()`
   */
  carregarStatusWindowsScheduler(): void {
    this.flightService.getWindowsSchedulerStatus().subscribe({
      next: statusWin => this.windowsScheduler.set(statusWin),
      error: () => {}
    });
  }

  /**
   * Sincroniza manualmente todas as buscas ativas com o Agendador do Windows.
   * Exemplo: `sincronizarAgendadorWindows()`
   */
  sincronizarAgendadorWindows(): void {
    this.sincronizandoWindows.set(true);
    this.flightService.syncWindowsScheduler().subscribe({
      next: statusWin => {
        this.sincronizandoWindows.set(false);
        this.windowsScheduler.set(statusWin);
        this.showToast(statusWin.mensagem, 'success');
      },
      error: () => {
        this.sincronizandoWindows.set(false);
        this.showToast('Falha ao sincronizar com o Agendador do Windows.', 'error');
      }
    });
  }

  /**
   * Remove todas as tarefas do GilsonViagens do Agendador do Windows.
   * Exemplo: `limparAgendadorWindows()`
   */
  limparAgendadorWindows(): void {
    if (!confirm('Remover todas as tarefas automáticas do GilsonViagens no Windows?')) return;
    this.flightService.clearWindowsScheduler().subscribe({
      next: res => {
        this.carregarStatusWindowsScheduler();
        this.showToast(res.mensagem, 'info');
      },
      error: () => this.showToast('Falha ao limpar tarefas do Windows.', 'error')
    });
  }

  /**
   * Atualiza o filtro de trecho na aba Histórico e recarrega os registros.
   * Exemplo: `filtrarHistoricoPor(1)`
   */
  filtrarHistoricoPor(valorSelecionado: number | string | null): void {
    const vazio = valorSelecionado === null || valorSelecionado === '' || valorSelecionado === 'null';
    this.filtroBuscaHistorico.set(vazio ? null : Number(valorSelecionado));
    this.carregarHistorico();
  }

  /**
   * Expande ou recolhe o acordeão de um grupo de rota no histórico.
   * Exemplo: `toggleGrupoHistorico(1)`
   */
  toggleGrupoHistorico(idBusca: number): void {
    this.gruposRecolhidos.update(mapa => ({ ...mapa, [idBusca]: !mapa[idBusca] }));
  }

  /**
   * Alterna entre ativo e pausado para o monitoramento informado.
   * Exemplo: `toggleAtiva(cfg)`
   */
  toggleAtiva(cfg: ConfigBusca): void {
    if (!cfg.id) return;
    this.flightService.toggleConfig(cfg.id).subscribe({
      next: atualizado => {
        this.configs.update(lista => lista.map(c => c.id === atualizado.id ? { ...c, ativa: atualizado.ativa } : c));
        this.carregarStatusWindowsScheduler();
        this.showToast(`${atualizado.origem} ➔ ${atualizado.destino} ${atualizado.ativa ? 'ativado' : 'pausado'}.`, 'info');
      },
      error: () => this.showToast('Falha ao alterar status.', 'error')
    });
  }

  /**
   * Confirma e exclui um monitoramento de voo.
   * Exemplo: `excluirConfig(cfg)`
   */
  excluirConfig(cfg: ConfigBusca): void {
    if (!cfg.id || !confirm(`Remover monitoramento ${cfg.origem} ➔ ${cfg.destino}?`)) return;
    this.flightService.deleteConfig(cfg.id).subscribe({
      next: () => {
        this.configs.update(lista => lista.filter(c => c.id !== cfg.id));
        this.historico.update(lista => lista.filter(h => h.id_busca !== cfg.id));
        this.carregarStatusWindowsScheduler();
        this.showToast('Monitoramento removido.', 'success');
      },
      error: () => this.showToast('Falha ao remover.', 'error')
    });
  }

  /**
   * Dispara imediatamente a varredura de preços para um card específico.
   * Exemplo: `buscarAgora(cfg)`
   */
  buscarAgora(cfg: ConfigBusca): void {
    if (!cfg.id) return;
    this.buscandoId.set(cfg.id);
    this.showToast(`Buscando ${cfg.origem} ➔ ${cfg.destino}...`, 'info');
    this.flightService.buscarAgora(cfg.id).subscribe({
      next: res => this.concluirBuscaIndividual(res),
      error: erro => {
        this.buscandoId.set(null);
        this.showToast(`Erro: ${extrairMensagemErroHttp(erro, 'Falha na busca')}`, 'error');
      }
    });
  }

  private concluirBuscaIndividual(res: SearchResult): void {
    this.buscandoId.set(null);
    const resumo = res.menor_valor
      ? `R$ ${res.menor_valor.toFixed(2)} (${res.data_ida} a ${res.data_volta})${res.alerta_enviado ? ' 🚨 Telegram!' : ''}`
      : res.mensagem;
    this.showToast(resumo, res.menor_valor ? 'success' : 'info');
    this.carregarConfigs();
    this.carregarHistorico();
  }

  /**
   * Dispara a execução em segundo plano de todas as buscas ativas.
   * Exemplo: `dispararTodas()`
   */
  dispararTodas(): void {
    this.executandoTudo.set(true);
    this.flightService.executarTudo().subscribe({
      next: res => { this.executandoTudo.set(false); this.showToast(res.mensagem, 'info'); },
      error: () => { this.executandoTudo.set(false); this.showToast('Falha ao disparar buscas.', 'error'); }
    });
  }

  /**
   * Abre o modal limpo para criação de um novo monitoramento.
   * Exemplo: `abrirModalCriacao()`
   */
  abrirModalCriacao(): void {
    this.editandoConfigId.set(null);
    this.tipoData.set('intervalo');
    this.novaBusca.set(criarRascunhoPadraoBusca());
    this.showModalNovaBusca.set(true);
  }

  /**
   * Abre o modal preenchido com os dados de um monitoramento existente.
   * Exemplo: `abrirModalEdicao(cfg)`
   */
  abrirModalEdicao(cfg: ConfigBusca): void {
    if (!cfg.id) return;
    this.editandoConfigId.set(cfg.id);
    this.tipoData.set(cfg.data_inicio && cfg.data_fim ? 'intervalo' : 'mes');
    this.novaBusca.set({
      origem: cfg.origem,
      destino: cfg.destino,
      data_inicio: cfg.data_inicio || obterDataFuturaIso(5),
      data_fim: cfg.data_fim || obterDataFuturaIso(25),
      passo_dias: cfg.passo_dias || 3,
      estrategia_busca: cfg.estrategia_busca || 'passo',
      mes_foco: cfg.mes_foco || (new Date().getMonth() + 1),
      duracao_dias: cfg.duracao_dias || 5,
      valor_alvo: cfg.valor_alvo,
      apenas_direto: Boolean(cfg.apenas_direto),
      horarios_execucao: cfg.horarios_execucao || '09:00',
      agendar_no_windows: cfg.agendar_no_windows ?? true,
      ativa: cfg.ativa
    });
    this.showModalNovaBusca.set(true);
  }

  /**
   * Salva o monitoramento (criação ou edição) após validar os campos do modal.
   * Exemplo: `salvarNovaBusca()`
   */
  salvarNovaBusca(): void {
    const validacao = validarEMontarPayloadBusca(this.novaBusca(), this.tipoData());
    if (validacao.erro || !validacao.payload) {
      this.showToast(validacao.erro || 'Dados inválidos.', 'error');
      return;
    }
    const idEdicao = this.editandoConfigId();
    if (idEdicao !== null) {
      this.executarAtualizacaoConfig(idEdicao, validacao.payload);
      return;
    }
    this.executarCriacaoConfig(validacao.payload);
  }

  private executarAtualizacaoConfig(idEdicao: number, payload: Partial<ConfigBusca>): void {
    this.flightService.updateConfig(idEdicao, payload).subscribe({
      next: atualizada => {
        this.configs.update(lista => lista.map(c => c.id === idEdicao ? atualizada : c));
        this.showModalNovaBusca.set(false);
        this.editandoConfigId.set(null);
        this.carregarStatusWindowsScheduler();
        this.showToast('Monitoramento e horários atualizados!', 'success');
      },
      error: erro => this.showToast(`Erro: ${extrairMensagemErroHttp(erro, 'Falha ao atualizar')}`, 'error')
    });
  }

  private executarCriacaoConfig(payload: Partial<ConfigBusca>): void {
    this.flightService.createConfig(payload).subscribe({
      next: nova => {
        this.configs.update(lista => [...lista, nova]);
        this.showModalNovaBusca.set(false);
        this.carregarStatusWindowsScheduler();
        this.showToast('Monitoramento criado e agendado!', 'success');
      },
      error: erro => this.showToast(`Erro: ${extrairMensagemErroHttp(erro, 'Falha ao criar')}`, 'error')
    });
  }

  /**
   * Atualiza parcialmente o signal de configurações do sistema.
   * Exemplo: `patchSettings({ horario_execucao: '08:00' })`
   */
  patchSettings(parcial: Partial<SystemSettings>): void {
    this.settings.update(atual => ({ ...atual, ...parcial }));
  }

  /**
   * Persiste as configurações globais do sistema no backend.
   * Exemplo: `salvarSettings()`
   */
  salvarSettings(): void {
    this.flightService.saveSettings(this.settings()).subscribe({
      next: salvo => { this.settings.set(salvo); this.showToast('Configurações salvas!', 'success'); },
      error: () => this.showToast('Falha ao salvar configurações.', 'error')
    });
  }

  /**
   * Envia uma notificação de teste para o Telegram configurado.
   * Exemplo: `testarTelegram()`
   */
  testarTelegram(): void {
    this.testandoTelegram.set(true);
    const cfg = this.settings();
    this.flightService.testTelegram(cfg.telegram_bot_token || '', cfg.telegram_chat_id || '').subscribe({
      next: res => { this.testandoTelegram.set(false); this.showToast(res.mensagem, res.sucesso ? 'success' : 'error'); },
      error: erro => {
        this.testandoTelegram.set(false);
        this.showToast(`Falha: ${extrairMensagemErroHttp(erro, 'Erro de conexão')}`, 'error');
      }
    });
  }
}
