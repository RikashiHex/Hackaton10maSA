"""Consultas SQL para residuos y categorías."""
from database.connection import get_connection


class ResiduoRepository:
    def categories(self):
        with get_connection() as con:
            return con.execute("SELECT * FROM categorias ORDER BY nombre").fetchall()

    def category(self, category_id):
        with get_connection() as con:
            return con.execute("SELECT * FROM categorias WHERE id = ?", (category_id,)).fetchone()

    def save_category(self, data, category_id=None):
        with get_connection() as con:
            if category_id:
                con.execute("UPDATE categorias SET nombre=?, descripcion=?, tipo=? WHERE id=?", (*data, category_id))
                return category_id
            return con.execute("INSERT INTO categorias (nombre, descripcion, tipo) VALUES (?, ?, ?)", data).lastrowid

    def category_usage(self, category_id):
        with get_connection() as con:
            return con.execute("SELECT COUNT(*) FROM residuos WHERE categoria_id = ?", (category_id,)).fetchone()[0]

    def delete_category(self, category_id):
        with get_connection() as con:
            con.execute("DELETE FROM categorias WHERE id = ?", (category_id,))

    def residues(self, text="", category_id=None, state=None):
        clauses, params = [], []
        if text:
            clauses.append("(r.nombre LIKE ? OR r.descripcion LIKE ? OR r.ubicacion LIKE ? OR r.notas LIKE ?)")
            params.extend([f"%{text}%"] * 4)
        if category_id:
            clauses.append("r.categoria_id = ?")
            params.append(category_id)
        if state:
            clauses.append("r.estado = ?")
            params.append(state)
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        query = """SELECT r.*, c.nombre AS categoria, c.tipo AS categoria_tipo
                   FROM residuos r JOIN categorias c ON c.id=r.categoria_id""" + where + " ORDER BY r.fecha_registro DESC, r.id DESC"
        with get_connection() as con:
            return con.execute(query, params).fetchall()

    def residue(self, residue_id):
        with get_connection() as con:
            return con.execute("SELECT * FROM residuos WHERE id=?", (residue_id,)).fetchone()

    def save_residue(self, data, residue_id=None):
        with get_connection() as con:
            if residue_id:
                con.execute("""UPDATE residuos SET nombre=?, descripcion=?, categoria_id=?, cantidad=?, unidad=?,
                               fecha_registro=?, ubicacion=?, estado=?, foto=?, notas=? WHERE id=?""", (*data, residue_id))
                return residue_id
            return con.execute("""INSERT INTO residuos
                (nombre, descripcion, categoria_id, cantidad, unidad, fecha_registro, ubicacion, estado, foto, notas)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", data).lastrowid

    def delete_residue(self, residue_id):
        with get_connection() as con:
            con.execute("DELETE FROM residuos WHERE id=?", (residue_id,))

    def summary(self):
        with get_connection() as con:
            total = con.execute("SELECT COUNT(*) FROM residuos").fetchone()[0]
            categories = con.execute("SELECT COUNT(*) FROM categorias").fetchone()[0]
            recyclable = con.execute("""SELECT COUNT(*) FROM residuos r JOIN categorias c ON c.id=r.categoria_id
                                      WHERE c.tipo='Reciclable'""").fetchone()[0]
            hazardous = con.execute("""SELECT COUNT(*) FROM residuos r JOIN categorias c ON c.id=r.categoria_id
                                     WHERE c.tipo='Peligroso'""").fetchone()[0]
            by_category = con.execute("""SELECT c.nombre, COUNT(r.id) total FROM categorias c
                                        LEFT JOIN residuos r ON r.categoria_id=c.id GROUP BY c.id HAVING total > 0
                                        ORDER BY total DESC, c.nombre""").fetchall()
            recent = con.execute("""SELECT r.*, c.nombre categoria FROM residuos r JOIN categorias c ON c.id=r.categoria_id
                                  ORDER BY r.fecha_registro DESC, r.id DESC LIMIT 5""").fetchall()
        return {"total": total, "categories": categories, "recyclable": recyclable, "hazardous": hazardous,
                "by_category": by_category, "recent": recent}
