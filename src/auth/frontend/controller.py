from typing import Any

from src.mybootstrap_ioc_itskovichanton.ioc import bean
from src.mybootstrap_ioc_itskovichanton.utils import default_dataclass_field
from src.mybootstrap_mvc_fastapi_itskovichanton.presenters import JSONResultPresenterImpl
from src.mybootstrap_mvc_itskovichanton.controller import Controller
from src.mybootstrap_mvc_itskovichanton.pipeline import Action
from src.mybootstrap_mvc_itskovichanton.result_presenter import ResultPresenter


@bean
class SendDailyBatchesAction(Action):
    batch_uploader: BatchUploader

    def run(self, request: Any = None, prev_result: Any = None) -> Any:
        return self.batch_uploader.process_daily(send=request["send"])


@bean
class SendBatchAction(Action):
    batch_uploader: BatchUploader

    def run(self, request: Any = None, prev_result: Any = None) -> Any:
        return self.batch_uploader.process_batch(request["batch"], request["send"])


@bean
class CheckAction(Action):
    batch_file_checker: BatchFileChecker

    def run(self, request: Any = None, prev_result: Any = None) -> Any:
        return self.batch_file_checker.check_batches()


@bean
class AuthController(Controller):
    default_result_presenter: ResultPresenter = default_dataclass_field(JSONResultPresenterImpl(exclude_unset=True))
    send_daily_batches_action: SendDailyBatchesAction
    send_batch_action: SendBatchAction
    check_action: CheckAction

    async def send_daily_batches(self, send: bool):
        return await self.run(self.send_daily_batches_action, call={"send": send})

    async def send_batch(self, batch: Batch, send: bool):
        return await self.run(self.send_batch_action, call={"batch": batch, "send": send})

    async def check(self):
        return await self.run(self.check_action, call={})
