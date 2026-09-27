from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from database import AsyncSessionLocal, Alumno, init_db
from schemas import AlumnoCreate, AlumnoUpdate, AlumnoOut

app = FastAPI(title="CRUD Alumno", version="1.0.0")

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

@app.on_event("startup")
async def startup():
    await init_db()

@app.get("/")
async def home():
    return {"mensaje": "API de alumnos funcionando correctamente"}

@app.post("/alumnos", response_model=AlumnoOut, status_code=status.HTTP_201_CREATED)
async def crear_alumno(alumno: AlumnoCreate, db: AsyncSession = Depends(get_db)):
    try:
        nuevo_alumno = Alumno(
            nombre=alumno.nombre,
            email=alumno.email,
            carrera=alumno.carrera,
        )
        db.add(nuevo_alumno)
        await db.commit()
        await db.refresh(nuevo_alumno)
        return nuevo_alumno
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un alumno con ese email",
        )

@app.get("/alumnos", response_model=List[AlumnoOut])
async def listar_alumnos(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Alumno))
    return result.scalars().all()

@app.get("/alumnos/{alumno_id}", response_model=AlumnoOut)
async def obtener_alumno(alumno_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Alumno).filter(Alumno.id == alumno_id))
    alumno = result.scalar_one_or_none()
    if not alumno:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alumno no encontrado",
        )
    return alumno

@app.put("/alumnos/{alumno_id}", response_model=AlumnoOut)
async def actualizar_alumno(alumno_id: int, alumno_update: AlumnoUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Alumno).filter(Alumno.id == alumno_id))
    alumno = result.scalar_one_or_none()
    if not alumno:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alumno no encontrado",
        )

    if alumno_update.nombre is not None:
        alumno.nombre = alumno_update.nombre
    if alumno_update.email is not None:
        alumno.email = alumno_update.email
    if alumno_update.carrera is not None:
        alumno.carrera = alumno_update.carrera

    try:
        await db.commit()
        await db.refresh(alumno)
        return alumno
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya existe",
        )

@app.delete("/alumnos/{alumno_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_alumno(alumno_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Alumno).filter(Alumno.id == alumno_id))
    alumno = result.scalar_one_or_none()
    if not alumno:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alumno no encontrado",
        )

    await db.delete(alumno)
    await db.commit()
    return None
