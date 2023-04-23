import basicauth
from src.mybootstrap_mvc_fastapi_itskovichanton.utils import get_call_from_request
from starlette.requests import Request

from src.mybootstrap_pyauth_itskovichanton.entities import Caller, AuthArgs, Session, User


def get_caller_from_request(request: Request) -> Caller:
    call = get_call_from_request(request)
    username = None
    password = None
    auth = request.headers.get("Authorization")
    if auth:
        username, password = basicauth.decode(auth)
    token = request.headers.get("sessionToken")
    auth_args = AuthArgs(session_token=token, username=username, password=password)

    if auth_args.empty():
        auth_args = None

    lang = request.headers.get("lang") or request.query_params.get("lang")
    return Caller(call=call,
                  auth_args=auth_args,
                  session=Session(account=User(
                      ip=call.ip,
                      username=username,
                      lang=lang, password=password),
                      token=token)
                  )
