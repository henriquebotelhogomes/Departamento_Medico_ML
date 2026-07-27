# Model Card — RadioAI Chest X-ray Classifier

## Model Details

| Field | Value |
|-------|-------|
| **Model type** | CNN (ResNet50 fine-tuned) |
| **Framework** | TensorFlow 2.21 / Keras 3.15 |
| **Input** | Imagem RGB 256×256 pixels |
| **Output** | 4 classes + OOD detection |
| **Parameters** | ~23.5M (ResNet50 backbone) + custom head |
| **Version** | 1.0.0 |
| **License** | MIT |

## Intended Use

- **Primary use:** Classificação de raios-X torácicos em 4 categorias
- **Classes:** Covid-19, Normal, Pneumonia Viral, Pneumonia Bacteriana
- **Usuários alvo:** Profissionais de saúde (como ferramenta auxiliar de triagem)
- **Limitações:** NÃO deve ser usado como diagnóstico definitivo

## Training Data

- **Dataset:** COVID-19 Radiography Database (Mendeley)
- **Pré-processamento:** Resize para 256×256, normalização via `resnet50.preprocess_input()`
- **Augmentation:** Nenhum (dataset já balanceado por subsampling)
- **Split:** Train / Val / Test (proporções do dataset original)

### Distribuição de Classes

| Classe | Descrição |
|--------|-----------|
| Covid-19 | Raios-X com padrão de opacidade bilateral (vidro fosco) |
| Normal | Raios-X torácicos sem achados patológicos |
| Viral Pneumonia | Infiltrados intersticiais difusos |
| Bacterial Pneumonia | Consolidação lobar ou segmentar |

## Architecture

```
Input (256×256×3)
  → ResNet50 (pretrained ImageNet, fine-tuned)
    → GlobalAveragePooling2D (2048-dim)
      → Dropout(0.3)
        → Dense(128, ReLU)
          → Dropout(0.3)
            → Dense(4, Softmax)
```

### Training Strategy

1. **Phase 1 (5 epochs):** Backbone frozen, head training with Adam(lr=1e-3)
2. **Phase 2 (25 epochs):** Full fine-tuning with Adam(lr=1e-5), EarlyStopping, ReduceLROnPlateau
3. **Class weights:** Computed via sklearn `compute_class_weight("balanced")`

## Metrics (Test Set)

> **Nota:** Execute `python training/evaluate.py` para gerar métricas atualizadas.

### Expected Performance Range

| Métrica | Valor Esperado |
|---------|---------------|
| Accuracy | 85-95% |
| F1 Score (macro) | 0.85-0.95 |
| F1 Score (weighted) | 0.85-0.95 |
| Mean AUC (one-vs-rest) | 0.95+ |

### Per-Class Metrics

| Classe | Precision | Recall | F1 | AUC |
|--------|-----------|--------|-----|-----|
| Covid-19 | — | — | — | — |
| Normal | — | — | — | — |
| Viral Pneumonia | — | — | — | — |
| Bacterial Pneumonia | — | — | — | — |

> Preencha com `python training/evaluate.py --model <path> --test-dir <path>`

## OOD (Out-of-Distribution) Detection

| Campo | Valor |
|-------|-------|
| **Método** | Cosine similarity no espaço de embeddings (GAP layer, 2048-dim) |
| **Threshold** | 0.45 |
| **Referência** | 9 imagens de raio-X reais (examples/) |
| **Comportamento** | Imagens com similaridade < 0.45 são marcadas como OOD |

### Resultados Empíricos

| Tipo de imagem | Similaridade típica | Classificação |
|---|---|---|
| Raio-X Covid real | 0.76 | In-distribution ✓ |
| Raio-X Normal real | 0.90 | In-distribution ✓ |
| Imagem de texto aleatório | 0.28 | OOD detectado ✓ |

> Para validação estatística completa: `python training/validate_ood_threshold.py`

## Explainability (Grad-CAM)

| Campo | Valor |
|-------|-------|
| **Método** | Gradient-weighted Class Activation Mapping |
| **Implementation** | tf.GradientTape manual (nested Functional model) |
| **Target layer** | Última camada convolucional do ResNet50 |
| **Output** | Heatmap PNG (base64) sobreposto à imagem original |
| **Colormap** | Jet (custom, sem matplotlib dependency) |

### Interpretação

- **Vermelho/quente:** Regiões de alta ativação — onde o modelo "olhou" para decidir
- **Azul/frio:** Regiões irrelevantes para a predição
- **Uso clínico:** Ajuda o médico a verificar se o modelo focou em áreas anatomicamente relevantes

## Ethical Considerations

### Bias e Limitações

- Modelo treinado em dataset específico — pode apresentar bias demográfico (idade, sexo, etnia não controlados)
- Dataset predominantemente de equipamentos específicos — generalização para outros fabricantes não garantida
- Performance em populações pediátricas não avaliada
- Radiografias AP vs. PA podem ter performance diferente

### Riscos

- **Falsos negativos:** Paciente com patologia classificado como Normal → risco de não-tratamento
- **Falsos positivos:** Paciente saudável classificado com patologia → ansiedade desnecessária, exames adicionais
- **OOD falha silenciosa:** Imagens médicas de outras regiões (abdômen, crânio) podem não ser detectadas como OOD

### Mitigações Implementadas

1. **OOD detection:** Rejeita imagens que não parecem raio-X torácico
2. **Grad-CAM:** Permite verificação visual humana da decisão
3. **Confidence display:** Mostra probabilidade por classe para avaliar incerteza
4. **Disclaimer:** Sistema explicitamente documentado como "ferramenta auxiliar"

## Limitations

1. Apenas 4 classes — não detecta outras patologias pulmonares (tuberculose, câncer, pneumotórax)
2. Sensível à qualidade da imagem (rotação, recorte excessivo, baixo contraste)
3. Não valida orientação da imagem (espelhada, invertida)
4. OOD detection pode falhar com imagens médicas de anatomia similar (ex: raio-X abdominal superior)
5. Não avaliado com imagens de dispositivos móveis ou fotografias de tela
6. Single-label — não suporta diagnósticos concomitantes

## Reproducibility

```bash
# Instalar dependências de treino
cd training
pip install -r requirements.txt

# Treinar (requer dataset)
python train.py --config config.yaml

# Avaliar
python evaluate.py --model ../models/chest_xray_model.keras --test-dir ../data/chest_xray/test

# Validar threshold OOD
python validate_ood_threshold.py
```

## References

- He et al., "Deep Residual Learning for Image Recognition" (2015)
- Selvaraju et al., "Grad-CAM: Visual Explanations from Deep Networks" (2017)
- COVID-19 Radiography Database, Kaggle/Mendeley
