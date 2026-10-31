# CS2 Video Stretcher

Aplicativo para Windows que converte gravações de gameplay do Counter-Strike 2 para widescreen esticado. O FFmpeg redimensiona o quadro inteiro, sem cortar a imagem nem adicionar barras pretas.

## Baixar para Windows

[Baixar o instalador do CS2 Video Stretcher 0.1.0](release/CS2VideoStretcher-Setup-0.1.0.exe). O instalador inclui o aplicativo, o FFmpeg e o FFprobe; não é necessário localizar ou instalar essas ferramentas separadamente.

O pacote inclui uma compilação do FFmpeg com suporte a `libx264`. Os avisos de licença e as informações da compilação estão instalados junto ao aplicativo, na pasta `Licencas`.

## Estado atual

A versão funcional atual permite selecionar um vídeo, consultar resolução e duração, escolher resolução de saída, qualidade CRF e pasta de destino, além de acompanhar o progresso da conversão. Processamento em lote, NVENC, histórico, configurações salvas e pré-visualização ainda não foram implementados.

## Requisitos

- Windows 11 (o app também pode funcionar em outros sistemas com Tkinter)
- Python 3.10 ou superior, com Tkinter
- FFmpeg e FFprobe disponíveis no `PATH`

## Instalação e execução

No PowerShell, na pasta do projeto:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
python -m cs2_stretcher
```

O app não requer pacotes Python de terceiros para funcionar. Instale o FFmpeg separadamente e adicione ao `PATH` do Windows a pasta que contém `ffmpeg.exe` e `ffprobe.exe`. O app também procura algumas pastas comuns de instalação.

## Como usar

1. Selecione um vídeo de gameplay.
2. Confira a resolução e a duração detectadas.
3. Escolha a resolução de saída e a qualidade. Um CRF menor gera mais qualidade e arquivos maiores.
4. Escolha a pasta de destino e inicie a conversão.

Por exemplo, uma gravação 1440×1080 exportada em 1920×1080 é esticada horizontalmente para 16:9. O quadro inteiro é mantido; os elementos ficam mais largos de propósito.

## Estrutura do projeto

```text
cs2_stretcher/       Aplicativo, interface, leitura e conversão de mídia
tests/               Testes automatizados
.github/             Integração contínua e modelos de issues
```

## Testes

```powershell
py -3.12 -m pip install -e ".[dev]"
py -3.12 -m pytest
```

## Criar um executável para Windows

A configuração do PyInstaller está planejada; ainda não há executável distribuível. A inclusão e a distribuição do FFmpeg/FFprobe também precisam ser definidas antes de uma versão de lançamento.

## Licença

MIT. Consulte [LICENSE](LICENSE).
