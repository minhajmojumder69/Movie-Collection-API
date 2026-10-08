from fastapi import FastAPI,Depends, HTTPException, Query,Body
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import model
from model import Movies
from typing import Annotated, Optional ,Literal
from database import engine,SessionLocal
from fastapi.responses import JSONResponse

app = FastAPI()

model.Base.metadata.create_all(bind=engine)

class Movie(BaseModel):
    title : str
    director : str
    genre : Literal["action", "comedy", "drama", "thriller"]
    duration : int = Field(gt=0)
    rating : float = Field(gt=0,lt=6)

class MovieUpdate(BaseModel):
    title : Optional[str] = Field(default=None)
    director : Optional[str] = Field(default=None)
    genre : Optional[str] = Literal["action", "comedy", "drama", "thriller"]
    duration : Optional[int] = Field(default=None,gt=0)
    rating : Optional[float] = Field(default=None,gt=0,lt=6)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

database_dependency = Annotated[Session,Depends(get_db)]

@app.get('/movies')
def show_movies(db:database_dependency):
    return db.query(Movies).all() 

@app.get('/movies/sort')
def sorted_movie(db: database_dependency,sort_by: str = Query('rating'),order: str = Query('desc')):

    valid_fields =["duration","rating",]
    if sort_by not in valid_fields:
        raise HTTPException(status_code=404, detail= f"Invalid field, select from {valid_fields}")
    
    if order not in ['asc','desc']:
        raise HTTPException(status_code=404, detail= f"Choose asc or desc")

    sort_order = True if order == 'desc' else False

    sorted_movie = db.query(Movies).all()
    sorted_movie.sort(key=lambda x: getattr(x, sort_by), reverse = sort_order)

    return sorted_movie

@app.get('/movies/{movies_id}')
def specific_movies(db: database_dependency, movies_id : int):
    specific = db.query(Movies).filter(Movies.movie_id == movies_id).first()
    if specific is not None:
        return specific
    else:
        raise HTTPException(status_code=404, detail="Movie not found..")

@app.post('/create_movies')
def create(db : database_dependency, new_movie: Movie):
    movie_model = Movies(**new_movie.model_dump())
    db.add(movie_model)
    db.commit()
    return JSONResponse(status_code=201,content={'massage': 'Movies created'})

@app.put('/movies/{movie_id}')
def create(db : database_dependency, movies_id: int, update: MovieUpdate):
    movie = db.query(Movies).filter(Movies.movie_id == movies_id).first()
    if movie is None:
        raise HTTPException(status_code=404, detail='Movie not found..')
    
    updated = update.model_dump(exclude_unset=True)

    for key,value in updated.items():
        setattr(movie,key,value)

    db.commit()
    return JSONResponse(status_code=200,content={'massage': 'Movies Update'})


@app.delete('/movies/{movies_id}')
def delete(db: database_dependency, movies_id: int):
    movie = db.query(Movies).filter(Movies.movie_id == movies_id).first()
    if movie is None:
        raise HTTPException(status_code=404, detail="Movie not found")

    db.query(Movies).filter(Movies.movie_id == movies_id).delete()
    db.commit()
    return JSONResponse(status_code=200,content={'massage':'Movie deleted..'})