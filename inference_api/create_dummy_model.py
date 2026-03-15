from sklearn.ensemble import RandomForestClassifier
import numpy as np
import pickle

# generar datos falsos
X = np.random.rand(100, 10)
y = np.random.randint(1, 7, 100)

# entrenar modelo simple
model = RandomForestClassifier()
model.fit(X, y)

# guardar modelo
pickle.dump(model, open("model.pkl", "wb"))

print("Modelo dummy creado: model.pkl")