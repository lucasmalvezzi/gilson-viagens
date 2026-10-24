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
import { ResumoContagemLogs, ScraperLogEntry } from '../models/flight.model';
import { filtrarEOrdenarLogs } from '../utils/flight-search-planner';

@Component({
  selector: 'app-scraper-log-console',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
  imports: [CommonModule, FormsModule],
  templateUrl: './scraper-log-console.component.html'
})
export class ScraperLogConsoleComponent {
  readonly logs = input.required<ScraperLogEntry[]>();
  readonly resumoLogs = input.required<ResumoContagemLogs>();
  readonly carregando = input<boolean>(false);
  readonly raspagemEmAndamento = input<boolean>(false);
  readonly autoRefreshLogs = model<boolean>(true);

  readonly solicitarAtualizacao = output<void>();
  readonly solicitarLimpeza = output<void>();

  readonly filtroNivelLog = signal<string>('ALL');
  readonly buscaTextoLog = signal<string>('');
  readonly ordemMaisRecentePrimeiro = signal<boolean>(true);

  readonly logsFiltrados = computed(() =>
    filtrarEOrdenarLogs(
      this.logs(),
      this.filtroNivelLog(),
      this.buscaTextoLog(),
      this.ordemMaisRecentePrimeiro()
    )
  );

  /**
   * Inverte a direção de ordenação cronológica dos logs no terminal.
   * Exemplo: `component.alternarOrdemCronologica()`
   */
  alternarOrdemCronologica(): void {
    const atual = this.ordemMaisRecentePrimeiro();
    this.ordemMaisRecentePrimeiro.set(!atual);
  }

  /**
   * Localiza a primeira URL HTTP/HTTPS dentro da mensagem de log.
   * Exemplo: `extrairUrlDoLog('Consultando https://google.com/travel/flights')`
   */
  extrairUrlDoLog(mensagem: string): string | null {
    const match = mensagem.match(/https?:\/\/[^\s]+/);
    return match ? match[0] : null;
  }

  /**
   * Exporta as linhas de log atualmente filtradas em um arquivo `.log` para download.
   * Exemplo: `component.baixarArquivoLog()`
   */
  baixarArquivoLog(): void {
    const linhas = this.logsFiltrados().map(
      l => `${l.timestamp} [${l.level}] (${l.logger}) ${l.message}`
    );
    const blob = new Blob([linhas.join('\n')], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `scraper-logs-${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.log`;
    link.click();
    URL.revokeObjectURL(url);
  }
}
