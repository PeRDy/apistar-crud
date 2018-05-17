from typing import Any, Dict, List

from apistar import http
from apistar.exceptions import NotFound
from sqlalchemy.orm import Session

from apistar_crud.base import BaseResource
from apistar_crud.signature import Annotations, inject_params


class Resource(BaseResource):
    @classmethod
    def add_create(mcs, namespace: Dict[str, Any], model,
                   input_type, output_type, extra_params: Annotations):
        def create(session: Session, element: input_type) -> http.JSONResponse:
            """
            Create a new element for this resource.
            """
            record = model(**element)
            session.add(record)
            session.flush()
            return http.JSONResponse(output_type(record), status_code=201)

        inject_params(create, extra_params)
        namespace['create'] = create

    @classmethod
    def add_retrieve(mcs, namespace: Dict[str, Any], model,
                     input_type, output_type, extra_params: Annotations):
        def retrieve(session: Session, element_id: str) -> output_type:
            """
            Retrieve an element of this resource.
            """
            record = session.query(model).get(element_id)
            if record is None:
                raise NotFound

            return output_type(record)

        inject_params(retrieve, extra_params)
        namespace['retrieve'] = retrieve

    @classmethod
    def add_update(mcs, namespace: Dict[str, Any], model,
                   input_type, output_type, extra_params: Annotations):
        def update(session: Session, element_id: str, element: input_type) -> http.JSONResponse:
            """
            Update an element of this resource.
            """
            record = session.query(model).get(element_id)
            if record is None:
                raise NotFound

            for k, value in element.items():
                setattr(record, k, value)

            return http.JSONResponse(output_type(record), status_code=200)

        inject_params(update, extra_params)
        namespace['update'] = update

    @classmethod
    def add_delete(mcs, namespace: Dict[str, Any], model,
                   input_type, output_type, extra_params: Annotations):
        def delete(session: Session, element_id: str):
            """
            Delete an element of this resource.
            """
            session.query(model).filter_by(id=element_id).delete()
            return http.JSONResponse(None, status_code=204)

        inject_params(delete, extra_params)
        namespace['delete'] = delete

    @classmethod
    def add_list(mcs, namespace: Dict[str, Any], model,
                 input_type, output_type, extra_params: Annotations):
        def list_(session: Session) -> List[output_type]:
            """
            List resource collection.
            """
            return [output_type(record) for record in session.query(model).all()]

        namespace['list'] = list_

    @classmethod
    def add_drop(mcs, namespace: Dict[str, Any], model,
                 input_type, output_type, extra_params: Annotations):
        def drop(session: Session) -> http.JSONResponse:
            """
            Drop resource collection.
            """
            num_records = session.query(model).count()
            session.query(model).delete()
            return http.JSONResponse({'deleted': num_records}, status_code=204)

        namespace['drop'] = drop
