
CREATE TABLE IF NOT EXISTS Categorias (
    id INTEGER PRIMARY KEY AUTOINCREMENT, 
    nombre_categoria TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS Marcas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_marca TEXT NOT NULL
);


CREATE TABLE IF NOT EXISTS Productos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_categoria NUMERIC NOT NULL,
    id_marca NUMERIC NOT NULL,
    nombre TEXT NOT NULL,
    descripcion TEXT,
    precio REAL NOT NULL,
    FOREIGN KEY (id_categoria) REFERENCES Categorias(id),
    FOREIGN KEY (id_marca) REFERENCES Marcas(id)
);


CREATE TABLE IF NOT EXISTS Variantes_producto (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_producto NUMERIC NOT NULL, 
    calce REAL NOT NULL, 
    color TEXT NOT NULL,
    stock NUMERIC,
    FOREIGN KEY (id_producto) REFERENCES Productos(id)
);

