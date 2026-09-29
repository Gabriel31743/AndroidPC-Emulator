# AndroidPC-Emulator

Protótipo de um emulador Android para PC/Windows.

**Estado atual:** launcher/orquestrador desktop. Ele prepara a configuração e a inicialização de uma VM Android via QEMU, com ADB para instalar APKs. Você ainda precisa fornecer uma imagem Android compatível e o QEMU/ADB.

## Recursos
- Interface desktop
- RAM, CPU e resolução configuráveis
- Áudio e rede configuráveis
- Detecção de QEMU e ADB
- Instalação de APK por ADB
- Iniciar, reiniciar e desligar
- Área de logs

## Executar
1. Instale Python 3.11+.
2. Instale QEMU para Windows e Android SDK Platform Tools (ADB).
3. Coloque uma imagem Android x86_64 em `images/` e ajuste `config.json`.
4. Execute `python launcher.py`.

O projeto não distribui ROMs, APKs ou componentes proprietários.
