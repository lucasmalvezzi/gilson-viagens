export interface ConfigBusca {
  id?: number;
  origem: string;
  destino: string;
  mes_foco?: number | null;
  data_inicio?: string | null;
  data_fim?: string | null;
  passo_dias?: number;
  estrategia_busca?: string;
  duracao_dias: number;
  valor_alvo: number;
  apenas_direto?: boolean;
  horarios_execucao?: string;
  agendar_no_windows?: boolean;
  ativa: boolean;
  criado_em?: string;
  menor_preco_recente?: number | null;
  ultima_coleta?: string | null;
  link_recente?: string | null;
}

export interface EstimativaChamadasPayload {
  mes_foco?: number | null;
  data_inicio?: string | null;
  data_fim?: string | null;
  duracao_dias: number;
  passo_dias: number;
  estrategia_busca: string;
}

export interface EstimativaChamadas {
  total_chamadas: number;
  tempo_estimado_segundos: number;
  amostras: string[];
}

export interface EstimativaVisual {
  total: number;
  tempo: number;
  amostras: string[];
}

export interface HistoricoPreco {
  id: number;
  id_busca: number;
  data_coleta: string;
  data_ida: string;
  data_volta: string;
  valor: number;
  link_direto: string;
}

export interface GrupoHistoricoRota {
  id_busca: number;
  config?: ConfigBusca;
  origem: string;
  destino: string;
  cidadeOrigem?: string;
  cidadeDestino?: string;
  menorValor: number;
  itens: HistoricoPreco[];
}

export interface SystemSettings {
  telegram_bot_token?: string | null;
  telegram_chat_id?: string | null;
  horario_execucao: string;
  ultimo_status?: string | null;
  ultima_execucao?: string | null;
}

export interface SearchResult {
  config_id: number;
  origem: string;
  destino: string;
  menor_valor?: number | null;
  data_ida?: string | null;
  data_volta?: string | null;
  link?: string | null;
  alerta_enviado: boolean;
  mensagem: string;
}

export interface ScraperLogEntry {
  id: number;
  timestamp: string;
  level: 'INFO' | 'WARNING' | 'ERROR' | string;
  logger: string;
  message: string;
}

export interface ScraperLogResponse {
  total: number;
  logs: ScraperLogEntry[];
}

export interface ResumoContagemLogs {
  total: number;
  info: number;
  warn: number;
  err: number;
}

export interface WindowsScheduledTaskEntry {
  task_name: string;
  proximo_disparo: string;
  status: string;
}

export interface WindowsSchedulerStatus {
  suportado: boolean;
  total_tarefas: number;
  comando_standalone: string;
  tarefas: WindowsScheduledTaskEntry[];
  mensagem: string;
}
