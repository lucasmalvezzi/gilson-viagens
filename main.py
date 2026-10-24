# -*- coding: utf-8 -*-
import sys
import uvicorn


def iniciar_servidor_local(host: str = "127.0.0.1", porta: int = 8000) -> None:
    """
    Exibe o banner de texto no terminal e inicia o servidor Uvicorn local.
    Exemplo: `iniciar_servidor_local("127.0.0.1", 8000)`
    """
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print("=" * 60)
    print("INICIANDO GILSONVIAGENS - CACADOR DE PASSAGENS (LOCAL)")
    print(f"   Acesse o painel web em: http://{host}:{porta}")
    print(f"   Documentacao da API:    http://{host}:{porta}/docs")
    print("=" * 60)
    uvicorn.run("app.main:app", host=host, port=porta, reload=False)


if __name__ == "__main__":
    iniciar_servidor_local()
