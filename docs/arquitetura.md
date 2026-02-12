# Arquitetura

## Estrutura de modulos

- `rc_mechanism_generator/__init__.py`
  - `bl_info`, `register()`, `unregister()`.
- `rc_mechanism_generator/properties.py`
  - Definicao de `PropertyGroup` e binding em `Scene`.
- `rc_mechanism_generator/ui.py`
  - Painel principal e composicao de secoes da interface.
- `rc_mechanism_generator/operators.py`
  - Fluxos principais de geracao, validacao e exportacao.
- `rc_mechanism_generator/geometry/`
  - Primitivas e builders de malha.
- `rc_mechanism_generator/dfm/`
  - Interface specs e checks de printabilidade.
- `rc_mechanism_generator/utils/`
  - Utilitarios de Blender, validacao e matematica.

## Ciclo de vida

### Register

1. `properties.register()`
2. `operators.register()`
3. `ui.register()`

### Unregister

1. `ui.unregister()`
2. `operators.unregister()`
3. `properties.unregister()`

## Modelo de dados

Dados persistidos em `bpy.types.Scene`:

- `scene.rcgen_refs` (`RCGEN_References`)
- `scene.rcgen_settings` (`RCGEN_Settings`)
- `scene.rcgen_tolerances` (`RCGEN_Tolerances`)

## Fluxo de dados (alto nivel)

1. Usuario preenche referencias e hardpoints.
2. Operadores chamam validacoes de cena em `utils.validation`.
3. Builders em `geometry.builders` criam malhas.
4. Utilitarios em `utils.blender_utils` criam/atualizam objetos e metadados.
5. Checks DFM em `dfm.checks` avaliam geometrias geradas.
6. Export cria pacote de fabricacao com BOM, assembly e manifest.

## Convencoes de objetos gerados

- Prefixo: `RC_`
- Exemplos:
  - `RC_LCA_L`, `RC_LCA_R`
  - `RC_UCA_L`, `RC_UCA_R`
  - `RC_Knuckle_L`, `RC_Knuckle_R`
  - `RC_TieRod_L`, `RC_TieRod_R`
  - `RC_ShockBody_L`, `RC_ShockRod_L`, `RC_Spring_L`
- Metadados por objeto:
  - `rcgen_id`
  - `rcgen_side`
  - `rcgen_module`
  - `rcgen_params` (json)

## Colecoes

Criadas/garantidas sob `RC_GEN`:

- `FrontAxle`
- `Steering`
- `Shocks`
- `Debug`
- `ExportTemp` (durante export)

## Decisoes tecnicas importantes

- Interferencia por bbox para custo computacional baixo.
- Validacao de export orientada por checks DFM antes de escrever arquivos.
- Fallback de export STL:
  - `bpy.ops.export_mesh.stl` (quando disponivel)
  - `bpy.ops.wm.stl_export` (fallback)

## Pontos de extensao

- Novos checks DFM:
  - `dfm/checks.py`.
- Novos componentes geometricos:
  - `geometry/primitives.py`
  - `geometry/builders.py`.
- Novos operadores:
  - `operators.py` + registro em `classes`.
- Novas secoes UI:
  - `ui.py`.

