# Foxy Launcher (Android ARM64)

Launcher derivado mantido por **Daniel**. Projeto original: [Felipe Prado / SpartanPort](https://github.com/FelipePrado0/SpartanPort). Base Android ARM64: [zFitness/gow3_android, branch `arm`](https://github.com/zFitness/gow3_android/tree/arm).

## Galaxy S24 Ultra

Perfil inicial conservador para Snapdragon 8 Gen 3 / Adreno 750: 720p, 60 FPS, upscaler e RCAS desligados, leitura adiada da GPU desligada, shaders assíncronos ligados. Essas opções priorizam uma base estável; não são uma promessa de FPS. O driver Vulkan/Turnip e a temperatura do aparelho influenciam muito o resultado.

## Instalação

1. Instale o host nixport compatível com o pacote.
2. Compile ou obtenha o pacote nixport `<versão>.zip` nos artefatos de CI.
3. Importe o ZIP em **Biblioteca → Importar pacote Port** no nixport.
4. Abra o Foxy Launcher, selecione a pasta do dump próprio que contém `eboot.bin` e configure os gráficos.

Não inclui arquivos do jogo. Preserve os avisos de licença e os créditos do projeto original.

## Ajustes gráficos no Foxy Launcher

O painel do nixport expõe resolução interna, VSync, limite de FPS, teto do motor, quadros enfileirados,
compilação assíncrona de shaders, opções avançadas de leitura da GPU, qualidade de texturas,
filtragem anisotrópica, sombras, bloom, desfoque de movimento, profundidade de campo e nitidez RCAS.
FSR/TAA temporal e geração de quadros permanecem opt-in e experimentais; o perfil inicial não os
ativa automaticamente.

O grupo **Monitor de desempenho** permite ativar o painel na tela e escolher FPS, frametime,
upscaler, uso de GPU/CPU, RAM e VRAM, além de ajustar tamanho, posição, opacidade e formato. A
exibição de métricas de GPU/VRAM depende do que o driver Android disponibiliza; em GPUs móveis com
memória unificada, a VRAM pode não ser reportada separadamente.

Para o Snapdragon 8 Gen 3 / Adreno 750, comece em 720p, 60 FPS, 1 quadro enfileirado, VSync ligado
e upscaling desligado. Teste uma opção por vez e retorne ao perfil anterior caso surjam artefatos,
falhas Vulkan ou aquecimento excessivo.
