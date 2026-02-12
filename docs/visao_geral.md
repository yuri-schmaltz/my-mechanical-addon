# Visao Geral

## O que e

`RC Mechanism Generator` e um addon para Blender focado em gerar componentes mecanicos de suspensao e direcao para plataformas RC, com suporte a verificacoes basicas de imprimibilidade e exportacao de pacote de fabricacao.

## Objetivos do addon

- Gerar geometria parametrica de:
  - Suspensao (`LCA`, `UCA`, `Knuckle` opcional).
  - Direcao (`ServoHorn`, `TieRods`).
  - Amortecimento (`ShockBody`, `ShockRod`, `Spring`).
- Validar requisitos minimos de cena:
  - Referencias obrigatorias.
  - Hardpoints obrigatorios por lado (`L`/`R`).
- Rodar checks DFM basicos:
  - Non-manifold.
  - Minimo de parede.
  - Overhang aproximado.
  - Oversize de volume de impressao.
  - Interferencia por bounding box.
- Exportar manufacturing pack:
  - STL/3MF.
  - BOM (`csv` e `json`).
  - `ASSEMBLY.md`.
  - `manifest.json`.

## Escopo funcional

- Painel unico em `View3D > Sidebar > RC`.
- Operadores de geracao individual e global.
- Operadores de validacao.
- Auto-captura por nome para referencias e hardpoints.
- Auto-split de pecas grandes para volume de impressao.

## Escopo tecnico

- Blender API (`bpy`, `bmesh`, `mathutils`).
- Sem dependencia de rede ou subprocess.
- Dados persistidos em `Scene` (`rcgen_refs`, `rcgen_settings`, `rcgen_tolerances`).

## Compatibilidade declarada

- Minimo em `bl_info`: Blender `3.6.0`.
- Documentacao de produto cita suporte `3.6 LTS` e `4.x`.
- Testes recentes do projeto foram executados em `5.0.1`.

## Limitacoes atuais

- Checks de interferencia usam bbox, nao BVH.
- Validacoes cinematicas sao aproximadas.
- Undo/Redo precisa validacao final em sessao GUI interativa.
- Licenca do projeto ainda nao esta declarada.

