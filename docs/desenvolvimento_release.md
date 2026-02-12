# Desenvolvimento e Release

## Setup de desenvolvimento

## Requisitos

- Blender com Python API (`bpy`) para testes runtime.
- Python local para tarefas auxiliares.

## Estrutura principal

- `rc_mechanism_generator/`
- `examples/`
- `dist/`
- `docs/`

## Tipagem estatica

Arquivos existentes:
- `mypy.ini`
- `pyrightconfig.json`

Uso recomendado:
- validar tipagem antes de release.

## Fluxo de desenvolvimento recomendado

1. Alterar codigo no modulo apropriado:
   - UI: `ui.py`
   - Propriedades: `properties.py`
   - Fluxos operadores: `operators.py`
   - Geometria: `geometry/*`
   - DFM: `dfm/*`
2. Rodar validacao minima:
   - abrir Blender
   - validar `Generate All`
   - validar `Run Printability Checks`
   - validar `Export Manufacturing Pack`
3. Atualizar `dist/RC_Mechanism_Generator.zip`.
4. Atualizar documentacao em `docs/` e `README.md`.

## Testes recomendados

## Smoke headless

Exemplo base:

```powershell
C:\Blender\blender.exe --factory-startup -b --python examples/create_mock_scene.py
```

Para suite automatizada do projeto:
- `eval_runtime_blender.py`
- resultados em `eval_outputs/runtime_eval_results.json`

## Matriz minima de testes

- Blender 3.6 LTS
- Blender 4.x
- Blender 5.x

## Casos criticos

- Setup de referencias e hardpoints.
- `generate_all` / `update_all`.
- `run_printability_checks`.
- `export_manufacturing_pack`.
- persistencia (`save/open`).
- enable/disable repetido do addon.

## Qualidade e observabilidade

## Recomendacoes

- Adicionar CI com smoke headless.
- Definir testes de regressao para:
  - geometrias non-manifold
  - export STL/3MF
  - auto-split de pecas grandes
- Padronizar mensagens de erro com acao recomendada.

## Release

## Checklist de release

1. Atualizar versao em `bl_info`.
2. Gerar zip em `dist/`.
3. Validar instalacao limpa via zip.
4. Executar smoke E2E.
5. Revisar documentacao.
6. Publicar changelog.

## Compliance

- Declarar licenca do projeto (`LICENSE`) antes de distribuicao ampla.
- Revisar compatibilidade de licencas de dependencias (quando houver externas).

## Troubleshooting de desenvolvimento

## Export STL indisponivel

- Em alguns ambientes, `bpy.ops.export_mesh.stl` nao esta disponivel.
- O projeto usa fallback para `bpy.ops.wm.stl_export`.

## Undo/Redo em headless

- `bpy.ops.ed.undo/redo` pode falhar em background mode por contexto.
- Validar undo/redo em sessao GUI para conclusao final de UX.

