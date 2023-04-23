import basicauth
from src.mybootstrap_mvc_fastapi_itskovichanton.utils import get_call_from_request
from starlette.requests import Request

from src.mybootstrap_pyauth_itskovichanton.entities import Caller, AuthArgs, Session, User


def get_caller_from_request(request: Request) -> Caller:
    call = get_call_from_request(request)
    auth_args = AuthArgs(session_token=request.headers.get("sessionToken"))
    auth = request.headers.get("Authorization")
    if auth:
        auth_args.username, auth_args.password = basicauth.decode(auth)

    lang = request.headers.get("lang") or request.query_params.get("lang")
    r = Caller(call=call, auth_args=auth_args, session=Session(
        account=User(ip=call.ip, username=auth_args.username,
                     password=auth_args.password), token=auth_args.session_token), lang=lang)
    if auth_args.empty():
        r.auth_args = None
    return r
