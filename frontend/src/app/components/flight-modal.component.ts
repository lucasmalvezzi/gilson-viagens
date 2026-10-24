import {
  ChangeDetectionStrategy,
  Component,
  ViewEncapsulation,
  computed,
  input,
  model,
  output,
  signal
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AeroportoInfo } from '../models/airports.data';
import { ConfigBusca } from '../models/flight.model';
import {
  MESES_DO_ANO,
  adicionarHorarioNaLista,
  buscarInfoAeroporto,
  calcularEstimativaRequisicoes,
  extrairHorariosLista,
  filtrarAeroportosPorTermo,
  removerHorarioDaLista
} from '../utils/flight-search-planner';

@Component({
  selector: 'app-flight-modal',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
  imports: [CommonModule, FormsModule],
  templateUrl: './flight-modal.component.html'
})
export class FlightModalComponent {
  readonly editandoConfigId = input<number | null>(null);
  readonly novaBusca = model.required<Partial<ConfigBusca>>();
  readonly tipoData = model<'intervalo' | 'mes'>('intervalo');

  readonly cancelar = output<void>();
  readonly confirmarSalvar = output<void>();

  readonly meses = MESES_DO_ANO;
  readonly dropdownOrigemAberto = signal(false);
  readonly dropdownDestinoAberto = signal(false);
  readonly novoHorarioInput = signal<string>('18:00');

  readonly listaHorarios = computed(() =>
    extrairHorariosLista(this.novaBusca().horarios_execucao)
  );

  readonly sugestoesOrigem = computed(() =>
    filtrarAeroportosPorTermo(this.novaBusca().origem || '')
  );

  readonly sugestoesDestino = computed(() =>
    filtrarAeroportosPorTermo(this.novaBusca().destino || '')
  );

  readonly infoOrigemSelecionada = computed(() =>
    buscarInfoAeroporto(this.novaBusca().origem)
  );

  readonly infoDestinoSelecionado = computed(() =>
    buscarInfoAeroporto(this.novaBusca().destino)
  );

  readonly estimativa = computed(() =>
    calcularEstimativaRequisicoes(this.novaBusca(), this.tipoData())
  );

  /**
   * Atualiza parcialmente os campos do rascunho de busca.
   * Exemplo: `component.atualizarCampo({ valor_alvo: 600 })`
   */
  atualizarCampo(parcial: Partial<ConfigBusca>): void {
    const estadoAtual = this.novaBusca();
    this.novaBusca.set({ ...estadoAtual, ...parcial });
  }

  /**
   * Seleciona um aeroporto do dropdown e fecha a lista de sugestões.
   * Exemplo: `component.selecionarAeroporto('origem', aeroportoGru)`
   */
  selecionarAeroporto(campo: 'origem' | 'destino', aero: AeroportoInfo): void {
    this.atualizarCampo({ [campo]: aero.iata });
    if (campo === 'origem') {
      this.dropdownOrigemAberto.set(false);
      return;
    }
    this.dropdownDestinoAberto.set(false);
  }

  /**
   * Troca os valores atuais entre os campos de origem e destino.
   * Exemplo: `component.inverterOrigemDestino()`
   */
  inverterOrigemDestino(): void {
    const atual = this.novaBusca();
    this.atualizarCampo({
      origem: atual.destino || '',
      destino: atual.origem || ''
    });
  }

  /**
   * Fecha ambos os dropdowns de autocomplete de aeroportos.
   * Exemplo: `component.fecharDropdowns()`
   */
  fecharDropdowns(): void {
    this.dropdownOrigemAberto.set(false);
    this.dropdownDestinoAberto.set(false);
  }

  /**
   * Fecha os dropdowns e emite o evento de cancelamento do modal.
   * Exemplo: `component.fecharModal()`
   */
  fecharModal(): void {
    this.fecharDropdowns();
    this.cancelar.emit();
  }

  /**
   * Adiciona o horário digitado no seletor à lista de horários desta busca.
   * Exemplo: `component.adicionarHorarioBusca()`
   */
  adicionarHorarioBusca(): void {
    const atualizado = adicionarHorarioNaLista(
      this.novaBusca().horarios_execucao,
      this.novoHorarioInput()
    );
    this.atualizarCampo({ horarios_execucao: atualizado });
  }

  /**
   * Remove um horário específico da lista de horários desta busca.
   * Exemplo: `component.removerHorarioBusca('09:00')`
   */
  removerHorarioBusca(horario: string): void {
    const atualizado = removerHorarioDaLista(
      this.novaBusca().horarios_execucao,
      horario
    );
    this.atualizarCampo({ horarios_execucao: atualizado });
  }
}
