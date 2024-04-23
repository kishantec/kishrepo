import models, urls
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from controller import *
import json
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status, APIRouter
from controller import get_db
from typing import Dict
import uvicorn
import csv
import os
from fastapi import UploadFile, File
from fastapi import Request
from collections import defaultdict
from sqlToJson import *

models.Base.metadata.create_all(bind=engine)


app = FastAPI()


# CORS Middleware
origins = ["http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
@app.get("/api/healthchecker")
def root():
    return {"message": "The API is LIVE!!"}

# To get fields json from sql
@app.get("/api/sqlToJson", status_code=status.HTTP_200_OK)
def sqlToJsonFunc(sqlQuery:str):
    json_out = sqlToJson(sqlQuery)
    return json_out
    # return {'sqlQueryis':sqlQuery}

# To get sql from json
@app.get("/api/jsonToSql",status_code=status.HTTP_200_OK)
def jsonToSqlFunc(fieldDictList1:str):
    json_out = jsonToSql(fieldDictList1)
    return json_out

@app.post("/api/systems/upload", status_code=status.HTTP_201_CREATED)
async def create_system_from_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        contents = await file.read()
        decoded_content = contents.decode('utf-8').splitlines()
        #print("DECODED OUTPUT:",decoded_content)
        
        csv_reader = csv.DictReader(decoded_content)
        
        created_systems = []
        for row in csv_reader:
            #print("ROW:",row)
            #row = {key: value.lower() for key, value in row.items()}
            new_system = models.System(**row)
            db.add(new_system)
            created_systems.append(new_system)
        
        db.commit()
        
        return {"Status": "Success", "Systems": created_systems, "status_code": status.HTTP_201_CREATED}
    except Exception as e:
        return {"Status": "Failed", "Error": str(e), "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR}



@app.get("/api/systems", status_code=status.HTTP_200_OK)
def get_systems(
    db: Session = Depends(get_db), limit: int = 10, page: int = 1, search: str = ""
):
    skip = (page - 1) * limit

    systems = (
        db.query(models.System)
        .filter(models.System.domain_name.contains(search))
        #.limit(limit)
        .offset(skip)
        .all()
    )

    # Grouping systems by domain_name and table_name
    grouped_systems = defaultdict(lambda: defaultdict(list))
    for system in systems:
        grouped_systems[system.domain_name][system.table_name].append(system.field_name)

    # Converting grouped_systems to the desired format
    formatted_systems = []
    for domain, tables in grouped_systems.items():
        for table, fields in tables.items():
            formatted_systems.append({
                "domain_name": domain,
                "table_name": table,
                "field_names": fields,
            })

    return {"Status": "Success", "Results": len(formatted_systems), "systems": formatted_systems, "status_code": status.HTTP_200_OK}
    #return {"Status": "Success", "Results": len(systems), "systems": systems,"status_code":status.HTTP_200_OK}

@app.delete("/api/systems/{domain}", status_code=status.HTTP_200_OK)
def delete_system(domain: str, db: Session = Depends(get_db)):
    systems_query = db.query(models.System).filter(models.System.domain_name == domain)
    system = systems_query.first()
    if not system:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No system with this domain: {domain} found",
        )
    systems_query.delete(synchronize_session=False)
    db.commit()
    return {"Status": "Success", "Message": "domain deleted successfully","status_code":status.HTTP_200_OK}

@app.get("/api/systems/{domain}", status_code=status.HTTP_200_OK)
def get_system(domain: str, db: Session = Depends(get_db)):
    systems_query = db.query(models.System).filter(models.System.domain_name == domain)
    systems = systems_query.all()

    unique_systems = {}  
    for system in systems:
        system_key = (system.domain_name, system.table_name)  
        if system_key not in unique_systems:
            unique_systems[system_key] = {"domain_name": system.domain_name, "table_name": system.table_name, "field_names": []}
        unique_systems[system_key]["field_names"].append(system.field_name)

    formatted_systems = list(unique_systems.values())
    return {"Status": "Success", "DomainName": domain, "systems": formatted_systems,"status_code":status.HTTP_200_OK}
    #return {"Status": "Success", "DomainName": domain, "systems": systems,"status_code":status.HTTP_200_OK}
 
@app.get("/api/systems/{domain}/{tablename}", status_code=status.HTTP_200_OK)
def get_system(domain: str,tablename: str, db: Session = Depends(get_db)):
    systems_query = db.query(models.System).filter(models.System.domain_name == domain,models.System.table_name == tablename)
    systems = systems_query.all()

    unique_systems = {}  
    for system in systems:
        system_key = (system.domain_name, system.table_name)  
        if system_key not in unique_systems:
            unique_systems[system_key] = {"domain_name": system.domain_name, "table_name": system.table_name, "field_names": []}
        unique_systems[system_key]["field_names"].append(system.field_name)

    formatted_systems = list(unique_systems.values())
    

    if not systems:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No system with this Domain: '{domain}' & table:'{tablename}'  found",
        )
    return {"Status": "Success", "DomainName": domain, "systems": formatted_systems,"status_code":status.HTTP_200_OK}



@app.get("/api/systems/getfields/table/{tablename}", status_code=status.HTTP_200_OK)
def get_system_fields(tablename: str , db: Session = Depends(get_db)):
    systems_query = db.query(models.System).filter(models.System.table_name == tablename)
    systems = systems_query.all()

    field_names = [system.field_name for system in systems]

    if not field_names:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No fields found for Table: '{tablename}'.",
        )
    return {"Status": "Success", "TableName": tablename, "FieldNames": field_names, "status_code": status.HTTP_200_OK}




# @app.patch("/api/systems/{domain}/{tablename}", status_code=status.HTTP_202_ACCEPTED)
# def update_system(domain: str, tablename:str, payload: Dict[str,str], db: Session = Depends(get_db)):
#     systems_query = db.query(models.System).filter(models.System.domain_name == domain,models.System.table_name == tablename )
#     system = systems_query.first()

#     if not system:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=f"No System with this id: {id} found",
#         )
#     # update_data = payload.model_dump(exclude_unset=True)
#     # systems_query.filter(models.System.id == id).update(update_data, synchronize_session=False)
#     for key, value in payload.items():
#         setattr(system,key,value)
#     db.commit()
#     db.refresh(system)
#     return {"Status": "Success", "system": system,"status_code":status.HTTP_202_ACCEPTED}



# if __name__ == '__main__':
#     app.run(debug=True)
if __name__ == '__main__':
    # uvicorn.run(app,host='127.0.0.1',port=5000)  
    # https://codeassistapi.azurewebsites.net/
    uvicorn.run(app,host='codeassistapi.azurewebsites.net',port=5000)