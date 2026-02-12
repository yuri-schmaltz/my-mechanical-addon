# Referencia de Operadores

## Convencao

- Namespace Blender: `rcgen.*`
- Retornos padrao: `{'FINISHED'}` ou `{'CANCELLED'}`.
- Mensagens: `self.report({'INFO'|'WARNING'|'ERROR'}, ...)`.

## Captura e validacao

### `rcgen.capture_selected`

- Label: `Capture Selected`
- Objetivo: atribuir objeto ativo para um campo em `scene.rcgen_refs`.
- Entrada:
  - `target_path` (ex.: `refs.chassis_obj`)

### `rcgen.auto_capture_by_name`

- Label: `Auto Capture By Name`
- Objetivo: preencher referencias/hardpoints por nomes comuns.
- Considera:
  - `auto_capture_prefix`
  - `auto_capture_scope`

### `rcgen.validate_references`

- Label: `Validate References`
- Objetivo: validar referencias obrigatorias.

### `rcgen.validate_hardpoints`

- Label: `Validate Hardpoints`
- Objetivo: validar hardpoints obrigatorios.

### `rcgen.validate_all`

- Label: `Validate All`
- Objetivo: validacao global minima de cena para geracao.

## Geracao por modulo

### `rcgen.generate_suspension`
### `rcgen.update_suspension`

- Labels: `Generate Suspension`, `Update Suspension`
- Objetivo:
  - gerar/atualizar `LCA`, `UCA`, `Knuckle` (quando aplicavel).

### `rcgen.generate_steering`
### `rcgen.update_steering`

- Labels: `Generate Steering`, `Update Steering`
- Objetivo:
  - gerar/atualizar `ServoHorn` e `TieRods`.

### `rcgen.reinfer_shock_mounts`

- Label: `Reinfer Shock Mounts`
- Objetivo:
  - reconstruir shock mounts inferidos no modulo de shocks.

### `rcgen.generate_shocks`
### `rcgen.update_shocks`

- Labels: `Generate Shock/Spring`, `Update Shock/Spring`
- Objetivo:
  - gerar/atualizar `ShockBody`, `ShockRod`, `Spring`.

## DFM e export

### `rcgen.run_printability_checks`

- Label: `Run Printability Checks`
- Objetivo:
  - executar checks DFM para objetos gerados.
- Regras principais:
  - non-manifold (erro)
  - min wall (erro)
  - overhang (warning)
  - oversize print volume (warning/erro)
  - interferencia wheel well (warning)

### `rcgen.export_manufacturing_pack`

- Label: `Export Manufacturing Pack`
- Objetivo:
  - exportar pacote de fabricacao completo.
- Fluxo:
  1. validar existencia de objetos gerados.
  2. rodar checks DFM.
  3. opcionalmente splitar pecas grandes.
  4. exportar STL/3MF.
  5. gerar BOM, assembly e manifest.
- Fallback STL:
  - `export_mesh.stl`
  - `wm.stl_export`

## Operadores globais

### `rcgen.generate_all`

- Label: `Generate All`
- Sequencia:
  1. suspensao
  2. direcao
  3. shocks

### `rcgen.update_all`

- Label: `Update All`
- Sequencia:
  1. suspensao
  2. direcao
  3. shocks

### `rcgen.organize_collections`

- Label: `Organize Collections`
- Objetivo: garantir estrutura de colecoes `RC_GEN`.

## Erros comuns por operador

- `validate_*`: faltam refs/hardpoints obrigatorios.
- `generate_steering`: tie rod com comprimento insuficiente.
- `generate_shocks`: stroke maior que comprimento total.
- `run_printability_checks`: non-manifold e min wall abaixo do limite.
- `export_manufacturing_pack`: erro de check DFM previo ou exporter indisponivel.

