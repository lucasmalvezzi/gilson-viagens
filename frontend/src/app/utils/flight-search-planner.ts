import { AeroportoInfo, LISTA_AEROPORTOS } from '../models/airports.data';
import {
  ConfigBusca,
  EstimativaVisual,
  GrupoHistoricoRota,
  HistoricoPreco,
  ResumoContagemLogs,
  ScraperLogEntry
} from '../models/flight.model';

export const MESES_DO_ANO: ReadonlyArray<{ valor: number; nome: string }> = [
  { valor: 1, nome: 'Janeiro' }, { valor: 2, nome: 'Fevereiro' },
  { valor: 3, nome: 'Março' }, { valor: 4, nome: 'Abril' },
  { valor: 5, nome: 'Maio' }, { valor: 6, nome: 'Junho' },
  { valor: 7, nome: 'Julho' }, { valor: 8, nome: 'Agosto' },
  { valor: 9, nome: 'Setembro' }, { valor: 10, nome: 'Outubro' },
  { valor: 11, nome: 'Novembro' }, { valor: 12, nome: 'Dezembro' }
];

/**
 * Retorna a data futura somada em dias no formato ISO 'YYYY-MM-DD'.
 * Exemplo: `obterDataFuturaIso(5)`
 */
export function obterDataFuturaIso(dias: number): string {
  const alvo = new Date();
  alvo.setDate(alvo.getDate() + dias);
  return alvo.toISOString().split('T')[0];
}

/**
 * Formata um objeto Date como 'DD/MM'.
 * Exemplo: `formatarDiaMesCurto(new Date(2026, 10, 15))`
 */
export function formatarDiaMesCurto(dt: Date): string {
  const dia = String(dt.getDate()).padStart(2, '0');
  const mes = String(dt.getMonth() + 1).padStart(2, '0');
  return `${dia}/${mes}`;
}

/**
 * Retorna o nome por extenso do mês (1..12) ou string vazia.
 * Exemplo: `obterNomeMesPorNumero(11)` -> `'Novembro'`
 */
export function obterNomeMesPorNumero(numeroMes: number | null | undefined): string {
  const encontrado = MESES_DO_ANO.find(m => m.valor === numeroMes);
  return encontrado ? encontrado.nome : '';
}

/**
 * Remove acentos e normaliza o texto para minúsculas.
 * Exemplo: `normalizarTermoBusca('São Paulo')` -> `'sao paulo'`
 */
export function normalizarTermoBusca(texto: string): string {
  return (texto || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim();
}

function pontuarRelevanciaAeroporto(aero: AeroportoInfo, termoNorm: string): number {
  if (normalizarTermoBusca(aero.iata) === termoNorm) return 0;
  if (normalizarTermoBusca(aero.cidade).startsWith(termoNorm)) return 1;
  return 2;
}

function aeroportoCombinaComTermo(aero: AeroportoInfo, termoNorm: string): boolean {
  const campos = [aero.iata, aero.cidade, aero.nome, aero.uf, aero.regiao];
  return campos.some(campo => normalizarTermoBusca(campo).includes(termoNorm));
}

/**
 * Filtra e ordena até 10 aeroportos correspondentes ao termo digitado.
 * Exemplo: `filtrarAeroportosPorTermo('Campinas')`
 */
export function filtrarAeroportosPorTermo(
  termo: string,
  catalogo: AeroportoInfo[] = LISTA_AEROPORTOS
): AeroportoInfo[] {
  const termoNorm = normalizarTermoBusca(termo);
  if (!termoNorm) {
    return catalogo.slice(0, 12);
  }
  return catalogo
    .filter(aero => aeroportoCombinaComTermo(aero, termoNorm))
    .sort((a, b) => pontuarRelevanciaAeroporto(a, termoNorm) - pontuarRelevanciaAeroporto(b, termoNorm))
    .slice(0, 10);
}

/**
 * Busca os metadados completos de um aeroporto a partir da sigla IATA.
 * Exemplo: `buscarInfoAeroporto('GRU')`
 */
export function buscarInfoAeroporto(
  iata: string | undefined | null,
  catalogo: AeroportoInfo[] = LISTA_AEROPORTOS
): AeroportoInfo | undefined {
  if (!iata) return undefined;
  const codigo = iata.trim().toUpperCase();
  return catalogo.find(aero => aero.iata === codigo);
}

/**
 * Resolve o código IATA de 3 letras a partir do texto ou nome da cidade digitado.
 * Exemplo: `resolverCodigoIataPorTermo('João Pessoa')` -> `'JPA'`
 */
export function resolverCodigoIataPorTermo(
  valor: string | undefined,
  catalogo: AeroportoInfo[] = LISTA_AEROPORTOS
): string {
  if (!valor) return '';
  const limpo = valor.trim();
  const exato = catalogo.find(a => a.iata.toLowerCase() === limpo.toLowerCase());
  if (exato) return exato.iata;
  const sugeridos = filtrarAeroportosPorTermo(limpo, catalogo);
  if (sugeridos.length > 0 && limpo.length > 3) {
    return sugeridos[0].iata;
  }
  return limpo.toUpperCase();
}

function formatarAmostraIdaVolta(dataIda: Date, duracaoDias: number): string {
  const dataVolta = new Date(dataIda);
  dataVolta.setDate(dataVolta.getDate() + duracaoDias);
  return `${formatarDiaMesCurto(dataIda)} a ${formatarDiaMesCurto(dataVolta)}`;
}

function calcularIntervaloPersonalizado(
  inicio: Date,
  fim: Date,
  duracaoDias: number,
  estrategia: string,
  passoDias: number
): EstimativaVisual {
  const passo = (estrategia === 'todos' || estrategia === 'fins_de_semana') ? 1 : Math.max(1, passoDias);
  const cursor = new Date(inicio);
  const amostras: string[] = [];
  let total = 0;
  while (cursor <= fim) {
    const diaSemana = cursor.getDay();
    const elegivel = estrategia !== 'fins_de_semana' || diaSemana === 5 || diaSemana === 6;
    if (elegivel) {
      total++;
      if (amostras.length < 5) amostras.push(formatarAmostraIdaVolta(cursor, duracaoDias));
    }
    cursor.setDate(cursor.getDate() + passo);
  }
  return { total, tempo: Math.round(total * 2.5), amostras };
}

/**
 * Calcula a estimativa visual de chamadas e amostras para o modal de criação/edição.
 * Exemplo: `calcularEstimativaRequisicoes(novaBusca, 'intervalo')`
 */
export function calcularEstimativaRequisicoes(
  busca: Partial<ConfigBusca>,
  tipoData: 'intervalo' | 'mes'
): EstimativaVisual {
  if (tipoData !== 'intervalo') {
    const nomeMes = obterNomeMesPorNumero(busca.mes_foco);
    return { total: 4, tempo: 10, amostras: [`Todas as sextas-feiras de ${nomeMes}`] };
  }
  if (!busca.data_inicio || !busca.data_fim) {
    return { total: 0, tempo: 0, amostras: [] };
  }
  const inicio = new Date(`${busca.data_inicio}T00:00:00`);
  const fim = new Date(`${busca.data_fim}T00:00:00`);
  if (inicio > fim) return { total: 0, tempo: 0, amostras: [] };
  return calcularIntervaloPersonalizado(
    inicio,
    fim,
    Math.max(1, busca.duracao_dias || 5),
    busca.estrategia_busca || 'passo',
    busca.passo_dias || 3
  );
}

function construirGrupoHistorico(
  idBusca: number,
  itens: HistoricoPreco[],
  cfg: ConfigBusca | undefined
): GrupoHistoricoRota {
  const menorValor = Math.min(...itens.map(i => i.valor));
  return {
    id_busca: idBusca,
    config: cfg,
    origem: cfg ? cfg.origem : `Trecho #${idBusca}`,
    destino: cfg ? cfg.destino : '',
    cidadeOrigem: cfg ? buscarInfoAeroporto(cfg.origem)?.cidade : undefined,
    cidadeDestino: cfg ? buscarInfoAeroporto(cfg.destino)?.cidade : undefined,
    menorValor,
    itens
  };
}

/**
 * Agrupa os itens do histórico de preços por trecho monitorado.
 * Exemplo: `agruparHistoricoPorRota(historico, configs)`
 */
export function agruparHistoricoPorRota(
  historico: HistoricoPreco[],
  configs: ConfigBusca[]
): GrupoHistoricoRota[] {
  const cfgMap = new Map<number, ConfigBusca>();
  configs.forEach(c => { if (c.id) cfgMap.set(c.id, c); });
  const gruposMap = new Map<number, HistoricoPreco[]>();
  for (const item of historico) {
    const lista = gruposMap.get(item.id_busca) || [];
    lista.push(item);
    gruposMap.set(item.id_busca, lista);
  }
  return Array.from(gruposMap.entries()).map(
    ([idBusca, itens]) => construirGrupoHistorico(idBusca, itens, cfgMap.get(idBusca))
  );
}

/**
 * Filtra os registros de log por severidade e texto e aplica ordenação.
 * Exemplo: `filtrarEOrdenarLogs(logs, 'INFO', 'GRU', true)`
 */
export function filtrarEOrdenarLogs(
  logs: ScraperLogEntry[],
  nivel: string,
  termoBusca: string,
  recentePrimeiro: boolean
): ScraperLogEntry[] {
  const termo = termoBusca.trim().toLowerCase();
  const filtrados = logs.filter(item => {
    if (nivel !== 'ALL' && item.level !== nivel) return false;
    if (!termo) return true;
    return item.message.toLowerCase().includes(termo) || item.logger.toLowerCase().includes(termo);
  });
  return recentePrimeiro ? [...filtrados].reverse() : filtrados;
}

/**
 * Contabiliza totais de logs por severidade (INFO, WARNING, ERROR).
 * Exemplo: `contabilizarResumoLogs(logs)`
 */
export function contabilizarResumoLogs(logs: ScraperLogEntry[]): ResumoContagemLogs {
  let info = 0;
  let warn = 0;
  let err = 0;
  for (const item of logs) {
    if (item.level === 'INFO') info++;
    else if (item.level === 'WARNING') warn++;
    else if (item.level === 'ERROR') err++;
  }
  return { total: logs.length, info, warn, err };
}

/**
 * Extrai uma mensagem amigável de um erro HTTP sem usar o tipo `any`.
 * Exemplo: `extrairMensagemErroHttp(erro, 'Falha ao salvar')`
 */
export function extrairMensagemErroHttp(erro: unknown, fallback: string): string {
  const corpoErro = (erro as { error?: { detail?: unknown; mensagem?: string } })?.error;
  if (!corpoErro) return fallback;
  if (typeof corpoErro.mensagem === 'string') return corpoErro.mensagem;
  const detalhe = corpoErro.detail;
  if (typeof detalhe === 'string') return detalhe;
  if (Array.isArray(detalhe)) {
    return detalhe
      .map((item: { msg?: string }) => item.msg || JSON.stringify(item))
      .join(', ');
  }
  return fallback;
}

/**
 * Converte uma string CSV de horários ('08:00, 20:00') em lista ordenada sem duplicatas.
 * Exemplo: `extrairHorariosLista('09:00, 18:00')` -> `['09:00', '18:00']`
 */
export function extrairHorariosLista(horariosCsv: string | undefined | null): string[] {
  const bruto = (horariosCsv || '09:00').trim();
  const itens = bruto
    .split(',')
    .map(item => item.trim())
    .filter(item => /^\d{2}:\d{2}$/.test(item));
  const unicos = Array.from(new Set(itens)).sort();
  return unicos.length > 0 ? unicos : ['09:00'];
}

/**
 * Adiciona um novo horário HH:MM à string CSV de horários da busca.
 * Exemplo: `adicionarHorarioNaLista('09:00', '18:00')` -> `'09:00, 18:00'`
 */
export function adicionarHorarioNaLista(
  horariosAtuais: string | undefined,
  novoHorario: string
): string {
  const limpo = (novoHorario || '').trim();
  if (!/^\d{2}:\d{2}$/.test(limpo)) {
    return horariosAtuais || '09:00';
  }
  const lista = extrairHorariosLista(horariosAtuais);
  if (!lista.includes(limpo)) {
    lista.push(limpo);
  }
  return lista.sort().join(', ');
}

/**
 * Remove um horário específico da lista mantendo ao menos um horário ativo.
 * Exemplo: `removerHorarioDaLista('09:00, 18:00', '09:00')` -> `'18:00'`
 */
export function removerHorarioDaLista(
  horariosAtuais: string | undefined,
  horarioRemover: string
): string {
  const filtrados = extrairHorariosLista(horariosAtuais).filter(h => h !== horarioRemover);
  return filtrados.length > 0 ? filtrados.join(', ') : '09:00';
}

/**
 * Cria o objeto de rascunho padrão para o formulário de nova busca.
 * Exemplo: `criarRascunhoPadraoBusca()`
 */
export function criarRascunhoPadraoBusca(): Partial<ConfigBusca> {
  return {
    origem: '',
    destino: '',
    data_inicio: obterDataFuturaIso(5),
    data_fim: obterDataFuturaIso(25),
    passo_dias: 3,
    estrategia_busca: 'passo',
    mes_foco: new Date().getMonth() + 1,
    duracao_dias: 5,
    valor_alvo: 500,
    apenas_direto: false,
    horarios_execucao: '09:00',
    agendar_no_windows: true,
    ativa: true
  };
}

/**
 * Valida e monta o payload de ConfigBusca ou retorna mensagem de erro.
 * Exemplo: `validarEMontarPayloadBusca(rascunho, 'intervalo')`
 */
export function validarEMontarPayloadBusca(
  rascunho: Partial<ConfigBusca>,
  tipoData: 'intervalo' | 'mes'
): { payload?: Partial<ConfigBusca>; erro?: string } {
  const iataOrigem = resolverCodigoIataPorTermo(rascunho.origem);
  const iataDestino = resolverCodigoIataPorTermo(rascunho.destino);
  if (!iataOrigem || !iataDestino || !rascunho.valor_alvo || rascunho.valor_alvo <= 0) {
    return { erro: 'Preencha origem, destino e um preço alvo válido.' };
  }
  if (tipoData === 'intervalo' && (!rascunho.data_inicio || !rascunho.data_fim)) {
    return { erro: 'Informe a data de início e fim.' };
  }
  return {
    payload: {
      origem: iataOrigem,
      destino: iataDestino,
      mes_foco: tipoData === 'mes' ? Number(rascunho.mes_foco || 1) : null,
      data_inicio: tipoData === 'intervalo' ? rascunho.data_inicio : null,
      data_fim: tipoData === 'intervalo' ? rascunho.data_fim : null,
      passo_dias: Number(rascunho.passo_dias) || 3,
      estrategia_busca: rascunho.estrategia_busca || 'passo',
      duracao_dias: Number(rascunho.duracao_dias) || 5,
      valor_alvo: Number(rascunho.valor_alvo),
      apenas_direto: Boolean(rascunho.apenas_direto),
      horarios_execucao: extrairHorariosLista(rascunho.horarios_execucao).join(', '),
      agendar_no_windows: rascunho.agendar_no_windows ?? true,
      ativa: rascunho.ativa ?? true
    }
  };
}
