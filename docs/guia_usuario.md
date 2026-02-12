# Guia do Usuario

## Instalacao

1. Gerar ou usar o zip do addon:
   - `dist/RC_Mechanism_Generator.zip`
2. Blender:
   - `Edit > Preferences > Add-ons > Install...`
3. Selecionar o zip.
4. Ativar `RC Mechanism Generator`.
5. Abrir `3D Viewport > Sidebar (N) > RC`.

## Fluxo rapido recomendado

1. Definir `Projeto`.
2. Preencher `Referencias`.
3. Preencher `Pontos de Fixacao` (hardpoints).
4. Rodar:
   - `Validar Referencias`
   - `Validar Pontos`
5. Executar `Gerar Tudo`.
6. Ajustar parametros e executar `Atualizar Tudo` quando necessario.
7. Rodar `Rodar Verificacoes de Impressao`.
8. Rodar `Exportar Pacote de Fabricacao`.

## Checklist minimo de entrada

### Referencias obrigatorias

- `Chassis`
- `Wheel_L`
- `Wheel_R`
- `Servo`

### Hardpoints obrigatorios por lado (`L`/`R`)

- `LCA_In_Front_[L/R]`
- `LCA_In_Rear_[L/R]`
- `LCA_Out_[L/R]`
- `UCA_In_Front_[L/R]`
- `UCA_In_Rear_[L/R]`
- `UCA_Out_[L/R]`
- `SteeringArm_Point_[L/R]`

## Auto-captura por nome

Use:
- `Captura Automatica`
- `Prefixo de Captura`
- `Escopo` (`ALL`, `SELECTED`, `ACTIVE`)

Objetivo:
- Preencher automaticamente referencias e hardpoints com base em nomes comuns.

## Modulos da interface

### Projeto

Define escala, wheelbase, hardware padrao, volume de impressao e parametros base.

### Tolerancias

Controla folgas globais usadas na geracao de interfaces mecanicas:
- `clearance_sliding_mm`
- `clearance_press_mm`
- `hole_oversize_mm`
- `nut_trap_clearance_mm`
- `insert_pocket_clearance_mm`

### Referencias

Objetos de contexto da montagem.

### Pontos de Fixacao

Empties de geometria para suspensao e direcao por lado.

### Suspensao

Parametros de secao, diametros e geracao de knuckle.

### Direcao

Parametros de servo horn, tie rod e Ackermann.

### Amortecedor / Mola

Configuracao de shock mounts (manual/inferido), corpo, haste e mola.

### DFM / Exportacao

Checks de imprimibilidade e export do pacote de fabricacao.

## Saida de exportacao

Pasta de saida:
- `export_dir/rcgen_id/`

Arquivos tipicos:
- `*.stl`
- `BOM.csv`
- `BOM.json`
- `ASSEMBLY.md`
- `manifest.json`
- `*.3mf` (quando habilitado e disponivel)

## Troubleshooting

### Erro: Missing references

- Verificar `Referencias` obrigatorias.

### Erro: Missing hardpoints

- Verificar todos os hardpoints dos lados `L` e `R`.

### Erro: Tie rod impossible

- Ajustar `Servo Horn Length` ou `SteeringArm_Point`.

### Erro: Shock stroke larger than total length

- Reduzir `shock_stroke_mm` ou aumentar `shock_total_length_mm`.

### Erro: exporter STL indisponivel

- Em versoes novas do Blender, o addon usa fallback para `wm.stl_export`.
- Confirmar addon de export STL habilitado no Blender se necessario.

### Warning de overhang/interferencia

- Esses warnings sao aproximacoes.
- Revisar orientacao de impressao e geometria no scene context.

