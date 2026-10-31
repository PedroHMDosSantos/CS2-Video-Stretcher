# CS2 Video Stretcher

Aplicativo para Windows que estica vídeos para widescreen sem cortar a imagem nem adicionar barras pretas. Ele aceita gravações de qualquer jogo ou outro vídeo compatível com FFmpeg.

O projeto nasceu de um problema com clipes e gravações do Counter-Strike 2: eles podiam sair com barras pretas e sem o esticamento horizontal que aparecia durante o jogo. O app permite aplicar esse esticamento também ao vídeo gravado.

## Baixar para Windows

[Baixar o instalador do CS2 Video Stretcher 0.1.1](https://github.com/PedroHMDosSantos/CS2-Video-Stretcher/releases/download/v0.1.1/CS2VideoStretcher-Setup-0.1.1.exe). O instalador inclui o aplicativo, o FFmpeg e o FFprobe; não é necessário localizar ou instalar essas ferramentas separadamente.

O pacote inclui uma compilação do FFmpeg com suporte a `libx264`. Os avisos de licença e as informações da compilação estão instalados junto ao aplicativo, na pasta `Licencas`.

## Como usar

1. Instale e abra o aplicativo pelo instalador acima.
2. Selecione um vídeo compatível com FFmpeg, como uma gravação de gameplay.
3. Confira a resolução e a duração detectadas.
4. Escolha a resolução de saída e a qualidade. Um CRF menor gera mais qualidade e arquivos maiores.
5. Escolha a pasta de destino e inicie a conversão.

Por exemplo, uma gravação 1440×1080 exportada em 1920×1080 é esticada horizontalmente para 16:9. O quadro inteiro é mantido; os elementos ficam mais largos de propósito.

## Estado atual

A versão funcional atual permite selecionar um vídeo, consultar resolução e duração, escolher resolução de saída, qualidade CRF e pasta de destino, além de acompanhar o progresso da conversão. Processamento em lote, NVENC, histórico, configurações salvas e pré-visualização ainda não foram implementados.

## Requisitos para desenvolvimento

- Windows 11
- Python 3.12, com Tkinter
- FFmpeg e FFprobe disponíveis no `PATH` para executar pelo código-fonte

## Executar pelo código-fonte

No PowerShell, na pasta do projeto:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
python -m cs2_stretcher
```

O app não requer pacotes Python de terceiros para funcionar. Para executar pelo código-fonte, instale o FFmpeg e adicione ao `PATH` do Windows a pasta que contém `ffmpeg.exe` e `ffprobe.exe`.

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

## Instalador do Windows

O instalador do Windows **já está disponível**: [baixar CS2 Video Stretcher 0.1.0](https://github.com/PedroHMDosSantos/CS2-Video-Stretcher/releases/download/v0.1.0/CS2VideoStretcher-Setup-0.1.0.exe). Ele inclui o aplicativo, o FFmpeg e o FFprobe; para usar o instalador, não é necessário instalar Python ou configurar o `PATH`.

O instalador foi empacotado com PyInstaller e Inno Setup. Os avisos de licença e as informações do build do FFmpeg ficam disponíveis na pasta `Licencas` após a instalação.

## Licença

MIT. Consulte [LICENSE](LICENSE).
