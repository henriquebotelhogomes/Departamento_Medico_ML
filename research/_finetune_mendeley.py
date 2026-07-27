"""Fine-tuning curto do ultimo bloco (conv5) da ResNet50, a partir do modelo Mendeley.

- Carrega modelo_raiox_mendeley.keras (feature-extraction ja treinado).
- Descongela apenas conv5_block* (BatchNorm permanece congelada -> fine-tuning estavel).
- LR baixo (1e-5), poucas epocas, com EarlyStopping e checkpoint protegido por baseline.
- Salva o melhor em modelo_raiox_mendeley_ft.keras (NAO sobrescreve os anteriores).
- Reavalia no Test/ original (sem e com TTA) e compara.
"""
import os, json, time, numpy as np, tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

TRAIN_DIR = "Dataset_mendeley"
TEST_DIR = "Test"
IMG_SIZE = (256, 256)
BATCH_SIZE = 32
SEED = 42
VALIDATION_SPLIT = 0.15
IN_MODEL = "modelo_raiox_mendeley.keras"
OUT_MODEL = "modelo_raiox_mendeley_ft.keras"
RESULT_JSON = "_resultado_finetune.json"
EPOCHS = 5
FINE_TUNE_FROM = "conv5_block1_1_conv"
AUTOTUNE = tf.data.AUTOTUNE


def log(m): print(m, flush=True)


# ------------------------------------------------------------ datasets
train_ds = keras.utils.image_dataset_from_directory(
    TRAIN_DIR, validation_split=VALIDATION_SPLIT, subset="training",
    seed=SEED, image_size=IMG_SIZE, batch_size=BATCH_SIZE, label_mode="categorical")
val_ds = keras.utils.image_dataset_from_directory(
    TRAIN_DIR, validation_split=VALIDATION_SPLIT, subset="validation",
    seed=SEED, image_size=IMG_SIZE, batch_size=BATCH_SIZE, label_mode="categorical")
class_names = train_ds.class_names
log(f"classes: {class_names}")

data_augmentation = keras.Sequential([
    layers.RandomRotation(0.03),
    layers.RandomZoom(0.1),
    layers.RandomTranslation(0.05, 0.05),
    layers.RandomContrast(0.1),
], name="data_augmentation")

# augmentation so no treino (imagens em [0,255]; preprocess_input esta dentro do modelo)
train_ds = train_ds.map(lambda x, y: (data_augmentation(x, training=True), y),
                        num_parallel_calls=AUTOTUNE).prefetch(AUTOTUNE)
val_ds = val_ds.prefetch(AUTOTUNE)

# --------------------------------------------------------------- modelo
log(f"Carregando {IN_MODEL} ...")
model = keras.models.load_model(IN_MODEL)

# localiza a base ResNet50 (submodelo aninhado)
base = None
for lyr in model.layers:
    if isinstance(lyr, keras.Model) and len(lyr.layers) > 50:
        base = lyr
        break
if base is None:
    base = model.get_layer("resnet50")
log(f"Base encontrada: {base.name} ({len(base.layers)} camadas)")

# descongela conv5_block* (exceto BatchNorm)
base.trainable = True
set_trainable = False
n_treinaveis = 0
for lyr in base.layers:
    if lyr.name == FINE_TUNE_FROM:
        set_trainable = True
    if set_trainable and not isinstance(lyr, layers.BatchNormalization):
        lyr.trainable = True
        n_treinaveis += 1
    else:
        lyr.trainable = False
log(f"Camadas descongeladas (sem BN): {n_treinaveis} de {len(base.layers)}")

model.compile(optimizer=keras.optimizers.Adam(1e-5),
              loss="categorical_crossentropy", metrics=["accuracy"])

_, baseline_val = model.evaluate(val_ds, verbose=0)
log(f"val_accuracy antes do fine-tuning: {baseline_val:.4f}")

cbs = [
    keras.callbacks.ModelCheckpoint(OUT_MODEL, monitor="val_accuracy",
                                    save_best_only=True, verbose=1,
                                    initial_value_threshold=baseline_val),
    keras.callbacks.EarlyStopping(monitor="val_loss", patience=2,
                                  restore_best_weights=True, verbose=1),
    keras.callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.5,
                                      patience=1, min_lr=1e-7, verbose=1),
]

log("== Fine-tuning ==")
t0 = time.time()
hist = model.fit(train_ds, validation_data=val_ds, epochs=EPOCHS,
                 callbacks=cbs, verbose=2)
log(f"tempo de treino: {(time.time() - t0) / 60:.1f} min")
best_val = max(hist.history["val_accuracy"])
log(f"melhor val_accuracy: {best_val:.4f}")

# garante que usamos o melhor peso salvo
if os.path.exists(OUT_MODEL):
    log(f"Carregando melhor checkpoint salvo ({OUT_MODEL})")
    model = keras.models.load_model(OUT_MODEL)
else:
    log("Checkpoint nao superou baseline; salvando estado atual mesmo assim.")
    model.save(OUT_MODEL)

# --------------------------------------------------- avaliacao no Test/
log("== Avaliando no Test/ ==")
test_ds = keras.utils.image_dataset_from_directory(
    TEST_DIR, image_size=IMG_SIZE, batch_size=BATCH_SIZE,
    label_mode="categorical", shuffle=False)
test_names = test_ds.class_names

y_true, y_pred = [], []
for imgs, labels in test_ds:
    p = model.predict(imgs, verbose=0)
    y_pred.append(np.argmax(p, axis=1))
    y_true.append(np.argmax(labels.numpy(), axis=1))
y_true = np.concatenate(y_true); y_pred = np.concatenate(y_pred)
acc = float(np.mean(y_true == y_pred))
log(f"ACC sem TTA: {acc:.4f} ({acc:.1%})")

tta = keras.Sequential([
    layers.RandomRotation(0.03), layers.RandomZoom(0.1),
    layers.RandomTranslation(0.05, 0.05), layers.RandomContrast(0.1),
])
N_TTA = 10
y_true2, y_pred2 = [], []
for imgs, labels in test_ds:
    probs = model.predict(imgs, verbose=0)
    for _ in range(N_TTA):
        probs = probs + model.predict(tta(imgs, training=True), verbose=0)
    probs = probs / (N_TTA + 1)
    y_pred2.append(np.argmax(probs, axis=1))
    y_true2.append(np.argmax(labels.numpy(), axis=1))
y_true2 = np.concatenate(y_true2); y_pred2 = np.concatenate(y_pred2)
acc_tta = float(np.mean(y_true2 == y_pred2))
log(f"ACC com TTA ({N_TTA}x): {acc_tta:.4f} ({acc_tta:.1%})")

K = len(test_names)
cm = np.zeros((K, K), dtype=int)
for t, p in zip(y_true2, y_pred2):
    cm[t, p] += 1
log("Matriz de confusao (TTA), linhas=verdadeiro, colunas=predito:")
log("     " + " ".join(f"{c:>4}" for c in test_names))
for i, row in enumerate(cm):
    log(f"  {test_names[i]:>2} " + " ".join(f"{v:>4}" for v in row))

resultado = {
    "baseline_feature_extraction_sem_tta": 0.825,
    "baseline_feature_extraction_com_tta": 0.80,
    "ft_melhor_val_accuracy": float(best_val),
    "ft_test_acc_sem_tta": acc,
    "ft_test_acc_com_tta": acc_tta,
    "epocas": len(hist.history["loss"]),
    "camadas_descongeladas": int(n_treinaveis),
}
with open(RESULT_JSON, "w", encoding="utf-8") as f:
    json.dump(resultado, f, indent=2, ensure_ascii=False)
log(json.dumps(resultado, indent=2, ensure_ascii=False))
log("PRONTO.")
