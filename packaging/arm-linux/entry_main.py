#!/usr/bin/env python3
"""entry_main.py — entry.sh 的 config/info verb 实现（fexdroid 契约的 JSON 出口）。

用法：
  entry_main.py config schema                       <ini>
  entry_main.py config get                          <ini>
  entry_main.py config set                          <ini> <payload-json>
  entry_main.py info patches                        <patch_status.json>

schema 是动态的：game_dir 设了且能读出游戏身份（TITLE_ID/APP_VER）并找到
补丁 XML，才追加"补丁"组（每个可用补丁一个布尔项）——这就是与游戏目录的
联动：没设目录时该组不存在，设了之后 App 端重拉 schema 即出现。
分辨率/帧率等 ini 键由上游 run.py 直接从 SPARTAN_CONFIG 指向的本文件读，
无需 entry.sh 转接。
"""
import json
import sys
from copy import deepcopy
from pathlib import Path

TREE = Path(__file__).resolve().parent
if str(TREE / 'scripts') not in sys.path:
    sys.path.insert(0, str(TREE / 'scripts'))

# Configuração exibida pelo host nixport. Os textos desta edição são pt-BR.
# O schema é gerado dinamicamente: o grupo de patches só aparece depois que a pasta do jogo
# foi selecionada e sua identidade/versão pôde ser lida.
STATIC_GROUPS = [
    {"id": "game", "title": "Jogo", "items": [
      {"key": "game_dir", "title": "Pasta do jogo", "type": "file", "mode": "directory",
       "note": "Selecione a pasta que contém eboot.bin (por exemplo, CUSA01740). Depois disso, as opções de patches aparecem aqui."}]},
    {"id": "display", "title": "Tela e renderização 3D", "items": [
      {"key": "render_resolution", "title": "Resolução de renderização", "type": "enum",
       "enum": ["540p", "480p", "720p", "900p", "native", "1080p", "1440p", "1800p", "4K"],
       "labels": ["540p — desempenho extremo", "480p — desempenho máximo", "720p — equilibrado (recomendado)", "900p — mais nitidez", "Nativa (1080p)", "1080p — alta qualidade", "1440p — experimental", "1800p — experimental", "4K — experimental"],
       "default": "720p", "restart": True,
       "note": "Define a resolução interna do jogo. Resoluções maiores deixam a imagem mais nítida, mas exigem muito mais da Adreno 750 e aumentam o aquecimento. Comece em 720p; teste 900p ou 1080p somente se houver margem de desempenho."},
      {"key": "video_backend", "title": "Backend de vídeo", "type": "enum",
       "enum": ["auto", "x11", "wayland"],
       "labels": ["Automático (recomendado)", "X11 (Termux:X11)", "Wayland"],
       "default": "auto", "restart": True,
       "note": "Driver de vídeo SDL. Mantenha Automático, a menos que esteja solucionando um problema de exibição."},
      {"key": "vsync", "title": "Sincronização vertical (VSync)", "type": "boolean", "default": True,
       "restart": True,
       "note": "Sincroniza os quadros com a atualização da tela para reduzir cortes na imagem. Desativar pode diminuir a latência, mas causar tearing."}]},
    {"id": "performance", "title": "FPS e fluidez", "items": [
      {"key": "fps_limit", "title": "Limite de FPS", "type": "enum",
       "enum": ["30", "60", "100", "120", "144", "180", "240", "0"],
       "labels": ["30 FPS — economia", "60 FPS — recomendado", "100 FPS", "120 FPS", "144 FPS", "180 FPS", "240 FPS", "Sem limite"],
       "default": "60",
       "note": "Limite de apresentação. O FPS real também depende do limite do motor, do patch disponível, da GPU e da temperatura. Sem limite não significa que o jogo alcançará FPS maiores."},
      {"key": "engine_fps", "title": "Limite do motor do jogo", "type": "enum",
       "enum": ["60", "100", "120", "144", "180", "240"],
       "labels": ["60 FPS — mais estável", "100 FPS", "120 FPS", "144 FPS", "180 FPS", "240 FPS — experimental"],
       "default": "60", "restart": True,
       "note": "Define o teto de atualização da simulação por meio dos patches de FPS. O jogo pode ficar limitado a 60 FPS se o patch correspondente não existir para a versão do seu dump. Taxas maiores podem causar instabilidade ou aquecimento."},
      {"key": "frames_queued", "title": "Quadros enfileirados pela GPU", "type": "enum",
       "enum": ["1", "2", "0"],
       "labels": ["1 — menor latência (recomendado)", "2 — pode melhorar a fluidez", "Sem limite — experimental"],
       "default": "1", "restart": True,
       "note": "Controla quantos quadros a CPU pode deixar na fila da GPU. Um valor menor reduz a latência de entrada; valores maiores podem ajudar em alguns cenários, mas consumir mais memória."},
      {"key": "async_shaders", "title": "Compilar shaders em segundo plano", "type": "boolean", "default": True,
       "restart": True,
       "note": "Pode reduzir travamentos quando efeitos novos aparecem. Aumenta o uso da CPU durante a compilação."},
      {"key": "deferred_readback", "title": "Leitura adiada da GPU", "type": "boolean", "default": False,
       "restart": True, "advanced": True,
       "note": "Pode reduzir esperas da CPU, mas fica desativada por padrão no perfil ARM por precaução com drivers Vulkan móveis. Ative apenas para testar e volte a desativar se houver tela preta, travamentos ou artefatos."},
      {"key": "stale_readback", "title": "Reutilizar leitura do quadro anterior", "type": "boolean", "default": True,
       "restart": True, "advanced": True,
       "note": "Pode reduzir esperas da CPU reaproveitando dados do quadro anterior. Desative se notar iluminação, sombras ou objetos inconsistentes."},
      {"key": "readback_linear", "title": "Filtragem linear na leitura da GPU", "type": "boolean", "default": True,
       "restart": True, "advanced": True,
       "note": "Correção de leitura usada para evitar corrupção de texturas. Recomendado manter ativado."}]},
    {"id": "monitor", "title": "Monitor de desempenho", "items": [
      {"key": "show_fps", "title": "Ativar monitor na tela", "type": "boolean", "default": False,
       "note": "Exibe um painel durante o jogo. As métricas disponíveis dependem do suporte do backend e do driver."},
      {"key": "overlay_fps", "title": "Mostrar FPS", "type": "boolean", "default": True},
      {"key": "overlay_frametime", "title": "Mostrar tempo por quadro (frametime)", "type": "boolean", "default": True},
      {"key": "overlay_upscaler", "title": "Mostrar método de upscaling", "type": "boolean", "default": True},
      {"key": "overlay_gpu", "title": "Mostrar uso da GPU", "type": "boolean", "default": False,
       "note": "A leitura de uso da GPU pode não estar disponível em todos os drivers Android."},
      {"key": "overlay_cpu", "title": "Mostrar uso da CPU", "type": "boolean", "default": False},
      {"key": "overlay_ram", "title": "Mostrar uso da memória RAM", "type": "boolean", "default": False},
      {"key": "overlay_vram", "title": "Mostrar memória de vídeo (VRAM)", "type": "boolean", "default": False,
       "note": "Em GPUs móveis unificadas, a VRAM pode ser estimada ou não reportada separadamente."},
      {"key": "overlay_scale", "title": "Tamanho do monitor (%)", "type": "number", "min": 50, "max": 300, "step": 10, "default": 150},
      {"key": "overlay_corner", "title": "Posição do monitor", "type": "enum",
       "enum": ["0", "1", "2", "3"],
       "labels": ["Superior esquerdo", "Superior direito", "Inferior esquerdo", "Inferior direito"],
       "default": "1"},
      {"key": "overlay_opacity", "title": "Opacidade do monitor (%)", "type": "number", "min": 0, "max": 100, "step": 5, "default": 50},
      {"key": "overlay_layout", "title": "Formato do monitor", "type": "enum",
       "enum": ["0", "1"], "labels": ["Compacto", "Expandido"], "default": "0"}]},
    {"id": "quality", "title": "Qualidade gráfica e upscaling", "items": [
      {"key": "experimental_upscaler", "title": "Ativar upscaling temporal experimental", "type": "boolean", "default": False,
       "restart": True,
       "note": "O upscaling temporal ainda é experimental neste jogo. Mantenha desligado para a configuração mais conservadora. Ao ativar, você libera FSR 3.1/TAA e os presets abaixo; podem ocorrer artefatos, lentidão ou falhas dependendo do driver."},
      {"key": "upscaler", "title": "Método de upscaling", "type": "enum",
       "enum": ["off", "fsr3", "taa"],
       "labels": ["Desativado", "AMD FSR 3.1 — experimental", "TAA — experimental"],
       "default": "off", "restart": True,
       "note": "Só funciona quando 'Ativar upscaling temporal experimental' estiver ligado. FSR 3.1 reconstrói a imagem a partir de uma resolução interna menor; TAA aplica antisserrilhado temporal."},
      {"key": "preset", "title": "Escala interna do upscaling", "type": "enum",
       "enum": ["0", "5", "1", "2", "3", "4"],
       "labels": ["AA nativo — 100%", "Ultra qualidade — 77%", "Qualidade — 67%", "Equilibrado — 59%", "Desempenho — 50%", "Ultra desempenho — 33%"],
       "default": "0", "restart": True,
       "note": "Define a proporção da resolução interna antes da reconstrução. Percentuais menores podem aumentar o FPS, mas reduzem detalhes. Só tem efeito com upscaling temporal ativado."},
      {"key": "frame_generation", "title": "Geração de quadros", "type": "enum",
       "enum": ["off", "fsr"],
       "labels": ["Desativada", "AMD FSR — experimental"],
       "default": "off", "restart": True,
       "note": "Insere quadros gerados entre quadros renderizados. Pode aumentar o FPS exibido, mas não aumenta a velocidade da simulação e pode adicionar latência ou artefatos. Requer upscaling experimental e suporte do driver."},
      {"key": "object_motion", "title": "Vetores de movimento de objetos", "type": "boolean", "default": False,
       "restart": True, "advanced": True,
       "note": "Fornece dados de movimento de objetos ao upscaler. Deixe desligado se não estiver usando FSR ou se notar rastros e artefatos."},
      {"key": "texture_quality", "title": "Qualidade das texturas", "type": "enum",
       "enum": ["0", "1", "2", "3"],
       "labels": ["Alta (padrão do jogo)", "Média", "Baixa", "Muito baixa"],
       "default": "0",
       "note": "Controla o nível de detalhe das texturas. Reduzir pode ajudar no uso de memória, mas deixa superfícies mais borradas."},
      {"key": "anisotropy", "title": "Filtragem anisotrópica", "type": "enum",
       "enum": ["0", "2", "4", "8", "16"],
       "labels": ["Padrão do jogo", "2x", "4x", "8x", "16x"],
       "default": "0", "restart": True,
       "note": "Melhora a nitidez de pisos e superfícies vistas em ângulo. Valores maiores podem aumentar o custo gráfico."},
      {"key": "shadows", "title": "Sombras", "type": "boolean", "default": True,
       "note": "Ativa ou desativa as sombras do jogo. Desativar pode melhorar o desempenho, mas altera a aparência."},
      {"key": "bloom", "title": "Brilho difuso (Bloom)", "type": "boolean", "default": True,
       "note": "Controla o halo de luz em áreas brilhantes. Desativar reduz esse efeito visual."},
      {"key": "motion_blur", "title": "Desfoque de movimento", "type": "boolean", "default": True,
       "note": "Desativa o borrão aplicado à câmera e a objetos em movimento."},
      {"key": "depth_of_field", "title": "Profundidade de campo", "type": "boolean", "default": True,
       "note": "Controla o desfoque de objetos distantes, especialmente em cenas cinematográficas."},
      {"key": "rcas", "title": "Nitidez RCAS", "type": "boolean", "default": False,
       "restart": True, "advanced": True,
       "note": "Etapa extra de nitidez. Pode recuperar detalhes, mas exige processamento adicional. Desativada por padrão no perfil Android."},
      {"key": "rcas_strength", "title": "Intensidade da nitidez RCAS", "type": "number", "min": 0, "max": 100, "step": 5, "default": 75,
       "restart": True, "advanced": True,
       "note": "Força da nitidez RCAS em porcentagem. Só tem efeito quando RCAS está ativado."}]},
    {"id": "input", "title": "Controles", "items": [
      {"key": "pad_shim", "title": "Ponte de controle virtual", "type": "boolean", "default": True,
       "restart": True,
       "note": "Permite usar os botões de toque e controles externos. Não desative se estiver jogando pela tela."}]},
]


def patch_group(vals):
    """Retorna as opções de patches quando a pasta do jogo e o XML correspondente existem."""
    game = vals.get('game_dir')
    if not game:
        return None
    try:
        from patches import available_patches, game_sfo
        sfo = game_sfo(game)
        title, version = sfo.get('TITLE_ID'), sfo.get('APP_VER')
        if not title or not version:
            return None
        xmls = sorted(TREE.glob(f'patches/*{title}.xml'))
        if not xmls:
            return None
        names = sorted(available_patches(str(xmls[0]), version))
        items = [{"key": "patches_enabled", "title": "Escolher patches manualmente", "type": "boolean",
                  "default": False, "restart": True,
                  "note": "Ativado: aplica somente os patches marcados abaixo. Desativado: usa a seleção padrão dos arquivos de patch."}]
        for n in names:
            item = {"key": f"patch: {n}", "title": n, "type": "boolean", "default": False}
            if n.startswith('Resolution Patch'):
                item["note"] = "Patches de resolução e correção de textura são incompatíveis entre si; a substituição é automática."
            items.append(item)
        return {"id": "patches", "title": "Patches", "items": items}
    except Exception:
        return None


def build_schema(vals):
    groups = deepcopy(STATIC_GROUPS)
    patches = patch_group(vals)
    if patches:
        groups.append(patches)
    return {"groups": groups}


SCHEMA = {"groups": STATIC_GROUPS}   # Schema estático usado quando não há contexto do INI.


def index(schema):
    out = {}
    for g in schema["groups"]:
        for it in g["items"]:
            out[it["key"]] = it
    return out


def read_ini(path):
    vals = {}
    for line in open(path, encoding="utf-8", errors="replace"):
        line = line.strip()
        if not line or line.startswith(("#", ";")):
            continue
        if "=" in line:
            k, v = line.split("=", 1)
            vals[k.strip()] = v.strip()
    return vals


def write_ini(path, vals):
    import os
    import shutil
    shutil.copyfile(path, path + ".bak")
    known = index(SCHEMA)
    lines = []
    seen = set()
    for line in open(path, encoding="utf-8", errors="replace").read().splitlines():
        s = line.strip()
        key = s.split("=", 1)[0].strip() if "=" in s and not s.startswith(("#", ";")) else None
        if key is not None and key in known:          # schema 内键重写；不在 vals（null 重置）= 删行
            if key in vals:
                lines.append(f"{key}={vals[key]}")
                seen.add(key)
        else:                                          # 未知键原样保留（launcher 资产）
            lines.append(line)
    for k, v in vals.items():
        if k not in seen:
            lines.append(f"{k}={v}")
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    os.replace(tmp, path)


def die(msg):
    print(json.dumps({"error": msg}))
    raise SystemExit(1)


def typed(it, raw):
    """The ini string as the schema's JSON type (get 的出口；coerce 的逆运算）。"""
    if it["type"] == "boolean":
        return str(raw).strip().lower() in ("1", "true", "yes", "on")
    if it["type"] == "number":
        v = float(raw)
        return int(v) if v.is_integer() else v
    return raw


def current_values(known, ini_vals):
    """全部配置项的当前值（真 JSON 类型，含 schema 缺省）——get 的出口、set 响应的 values。"""
    out = {}
    for k, it in known.items():
        if k in ini_vals:
            try:
                out[k] = typed(it, ini_vals[k])
            except Exception:
                out[k] = it.get("default")
        elif "default" in it:
            out[k] = it.get("default")
    return out


# 补丁互斥（与 patches.py 的 EXCLUSIVE_PREFIX/REPLACED_BY_EXCLUSIVE 同义，此处独立成表：
# entry_main 在打包层不 import scripts，保持模板自包含）。
EXCLUSIVE_PREFIX = 'Resolution Patch'
REPLACED_BY_EXCLUSIVE = ('Bug Fix - Texture Corruption Fix',)


def apply_linkage(ini_vals):
    """联动副作用——业务规则的唯一住址（App 只渲染返回的状态，不认识任何规则）。
    勾选任一分辨率补丁时自动关闭被顶替的纹理修复。"""
    prefix = 'patch: '
    picks = [k[len(prefix):] for k in ini_vals
             if k.startswith(prefix) and ini_vals[k] == '1']
    if any(name.startswith(EXCLUSIVE_PREFIX) for name in picks):
        for name in REPLACED_BY_EXCLUSIVE:
            key = prefix + name
            if ini_vals.get(key) == '1':
                ini_vals[key] = '0'


def coerce(it, raw):
    t = it["type"]
    if t == "boolean":
        v = raw if isinstance(raw, bool) else str(raw).strip().lower() in ("1", "true", "yes", "on")
        return "1" if v else "0"
    if t == "number":
        v = float(raw)
        if "min" in it:
            v = max(it["min"], v)
        if "max" in it:
            v = min(it["max"], v)
        step = it.get("step")
        if step:
            digits = len(str(step).split(".")[-1]) if "." in str(step) else 0
            v = round(v, digits if digits < 3 else 3)
        return f"{v:g}"
    if t == "enum":
        choices = [str(c) for c in it["enum"]]
        v = str(raw)
        if v not in choices:
            raise ValueError(f"{it['key']}: {v!r} not in enum")
        return v
    return str(raw)


def main():
    argv = sys.argv[1:]
    ns = argv.pop(0) if argv else ""
    if ns == "config":
        sub = argv.pop(0) if argv else ""
        ini = argv.pop(0) if argv else ""
        if not ini:
            die("Os comandos config schema/get/set precisam do caminho do arquivo INI.")
        ini_vals = read_ini(ini)
        schema = build_schema(ini_vals)          # 动态：补丁组跟随 game_dir
        known = index(schema)
        if sub == "schema":
            print(json.dumps(schema))
            return
        if sub == "get":
            print(json.dumps(current_values(known, ini_vals)))
        elif sub == "set":
            payload = json.loads(argv[0]) if argv else {}
            if not isinstance(payload, dict):
                die("Os dados enviados precisam estar em formato de objeto JSON.")
            for k, v in payload.items():
                if k not in known:
                    die(f"Configuração não reconhecida: {k}")
                if v is None:                  # null = 重置（删行，get 回落到 schema 缺省）
                    ini_vals.pop(k, None)
                else:
                    ini_vals[k] = coerce(known[k], v)
            apply_linkage(ini_vals)            # 联动副作用：业务规则的唯一住址
            write_ini(ini, ini_vals)
            # Retorna o estado completo após salvar (valores + schema), incluindo alterações
            # automáticas de compatibilidade entre patches.
            schema = build_schema(ini_vals)
            print(json.dumps({"ok": True,
                              "written": {k: ini_vals.get(k) for k in payload},
                              "values": current_values(index(schema), ini_vals),
                              "schema": schema}))
        else:
            die("Uso: config schema|get|set")
    elif ns == "info":
        sub = argv.pop(0) if argv else ""
        if sub != "patches":
            die("Uso: info patches")
        path = argv[0] if argv else ""
        import os
        if not path or not os.path.isfile(path):
            print(json.dumps({"requested": [], "effective": {},
                              "note": "Inicie o jogo uma vez; o estado dos patches aparecerá depois da primeira execução."}))
            return
        d = json.load(open(path, encoding="utf-8"))
        applied = d.get("applied") or []
        req = [{"name": n, "status": "applied"} for n in applied]
        if d.get("reason"):
            req.append({"name": "patch selection", "status": "info", "reason": d["reason"]})
        eff = {"title_id": d.get("title_id"), "app_version": d.get("app_version"),
               "vulkan_status": d.get("vulkan_status"), "supported": d.get("supported")}
        for k in ("dmem_mb", "vblank_hz", "upscaler"):
            if k in d:
                eff[k] = d[k]
        print(json.dumps({"requested": req, "effective": eff}))
    else:
        die("usage: entry_main.py config|info …")


if __name__ == "__main__":
    main()
