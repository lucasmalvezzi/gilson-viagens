import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
  ConfigBusca,
  EstimativaChamadas,
  EstimativaChamadasPayload,
  HistoricoPreco,
  ScraperLogResponse,
  SearchResult,
  SystemSettings,
  WindowsSchedulerStatus
} from '../models/flight.model';

@Injectable({
  providedIn: 'root'
})
export class FlightService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = '/api';

  /**
   * Busca todas as configurações de monitoramento cadastradas.
   * Exemplo: `flightService.getConfigs().subscribe(...)`
   */
  getConfigs(): Observable<ConfigBusca[]> {
    const endpoint = `${this.apiUrl}/configs`;
    return this.http.get<ConfigBusca[]>(endpoint);
  }

  /**
   * Cria uma nova configuração de monitoramento no backend.
   * Exemplo: `flightService.createConfig({ origem: 'GRU', destino: 'JPA', valor_alvo: 800 })`
   */
  createConfig(payload: Partial<ConfigBusca>): Observable<ConfigBusca> {
    const endpoint = `${this.apiUrl}/configs`;
    return this.http.post<ConfigBusca>(endpoint, payload);
  }

  /**
   * Atualiza uma configuração existente pelo seu identificador numérico.
   * Exemplo: `flightService.updateConfig(1, { valor_alvo: 700 })`
   */
  updateConfig(id: number, payload: Partial<ConfigBusca>): Observable<ConfigBusca> {
    const endpoint = `${this.apiUrl}/configs/${id}`;
    return this.http.put<ConfigBusca>(endpoint, payload);
  }

  /**
   * Alterna o estado ativo/pausado de um monitoramento.
   * Exemplo: `flightService.toggleConfig(1)`
   */
  toggleConfig(id: number): Observable<ConfigBusca> {
    const endpoint = `${this.apiUrl}/configs/${id}/toggle`;
    return this.http.patch<ConfigBusca>(endpoint, {});
  }

  /**
   * Remove permanentemente um monitoramento e seu histórico.
   * Exemplo: `flightService.deleteConfig(1)`
   */
  deleteConfig(id: number): Observable<void> {
    const endpoint = `${this.apiUrl}/configs/${id}`;
    return this.http.delete<void>(endpoint);
  }

  /**
   * Dispara uma varredura imediata no Google Flights para o trecho informado.
   * Exemplo: `flightService.buscarAgora(1)`
   */
  buscarAgora(id: number): Observable<SearchResult> {
    const endpoint = `${this.apiUrl}/configs/${id}/buscar-agora`;
    return this.http.post<SearchResult>(endpoint, {});
  }

  /**
   * Consulta o histórico de preços coletados, opcionalmente filtrado por trecho.
   * Exemplo: `flightService.getHistorico(1, 100, 0)`
   */
  getHistorico(
    idBusca?: number | string | null,
    limit = 100,
    offset = 0
  ): Observable<HistoricoPreco[]> {
    let params = new HttpParams()
      .set('limit', limit.toString())
      .set('offset', offset.toString());
    if (idBusca !== undefined && idBusca !== null && idBusca !== '' && String(idBusca) !== 'null') {
      params = params.set('id_busca', String(idBusca));
    }
    return this.http.get<HistoricoPreco[]>(`${this.apiUrl}/historico`, { params });
  }

  /**
   * Solicita ao backend a estimativa de chamadas para os parâmetros de busca.
   * Exemplo: `flightService.estimarChamadas(payload)`
   */
  estimarChamadas(payload: EstimativaChamadasPayload): Observable<EstimativaChamadas> {
    const endpoint = `${this.apiUrl}/configs/estimar-chamadas`;
    return this.http.post<EstimativaChamadas>(endpoint, payload);
  }

  /**
   * Carrega as configurações globais do sistema (Telegram e agendamento).
   * Exemplo: `flightService.getSettings()`
   */
  getSettings(): Observable<SystemSettings> {
    const endpoint = `${this.apiUrl}/settings`;
    return this.http.get<SystemSettings>(endpoint);
  }

  /**
   * Salva as configurações globais do sistema e atualiza o cronjob.
   * Exemplo: `flightService.saveSettings(settings)`
   */
  saveSettings(settings: SystemSettings): Observable<SystemSettings> {
    const endpoint = `${this.apiUrl}/settings`;
    return this.http.post<SystemSettings>(endpoint, settings);
  }

  /**
   * Dispara uma mensagem de teste para o Telegram Bot configurado.
   * Exemplo: `flightService.testTelegram('123:ABC', '999')`
   */
  testTelegram(
    token?: string,
    chatId?: string
  ): Observable<{ sucesso: boolean; mensagem: string }> {
    return this.http.post<{ sucesso: boolean; mensagem: string }>(
      `${this.apiUrl}/settings/test-telegram`,
      { token, chat_id: chatId }
    );
  }

  /**
   * Inicia em segundo plano a rotina completa para todos os monitoramentos ativos.
   * Exemplo: `flightService.executarTudo()`
   */
  executarTudo(): Observable<{ mensagem: string }> {
    const endpoint = `${this.apiUrl}/executar-tudo`;
    return this.http.post<{ mensagem: string }>(endpoint, {});
  }

  /**
   * Obtém os registros recentes de log estruturado do webscraper.
   * Exemplo: `flightService.getLogs(300)`
   */
  getLogs(limit = 300): Observable<ScraperLogResponse> {
    const params = new HttpParams().set('limit', limit.toString());
    return this.http.get<ScraperLogResponse>(`${this.apiUrl}/logs`, { params });
  }

  /**
   * Limpa o buffer de logs do webscraper.
   * Exemplo: `flightService.clearLogs()`
   */
  clearLogs(): Observable<{ mensagem: string }> {
    const endpoint = `${this.apiUrl}/logs`;
    return this.http.delete<{ mensagem: string }>(endpoint);
  }

  /**
   * Consulta as tarefas independentes registradas no Agendador do Windows.
   * Exemplo: `flightService.getWindowsSchedulerStatus()`
   */
  getWindowsSchedulerStatus(): Observable<WindowsSchedulerStatus> {
    const endpoint = `${this.apiUrl}/settings/windows-scheduler`;
    return this.http.get<WindowsSchedulerStatus>(endpoint);
  }

  /**
   * Sincroniza todas as buscas ativas com o Agendador de Tarefas do Windows.
   * Exemplo: `flightService.syncWindowsScheduler()`
   */
  syncWindowsScheduler(): Observable<WindowsSchedulerStatus> {
    const endpoint = `${this.apiUrl}/settings/windows-scheduler/sync`;
    return this.http.post<WindowsSchedulerStatus>(endpoint, {});
  }

  /**
   * Remove todas as tarefas do GilsonViagens registradas no Windows.
   * Exemplo: `flightService.clearWindowsScheduler()`
   */
  clearWindowsScheduler(): Observable<{ mensagem: string }> {
    const endpoint = `${this.apiUrl}/settings/windows-scheduler`;
    return this.http.delete<{ mensagem: string }>(endpoint);
  }
}
