from contextlib import contextmanager

from scripts.keepalive import run


class FakeSession:
    def __init__(self):
        self.values = iter([200, 10])

    def scalar(self, statement):
        return next(self.values)


def test_consulta_o_banco_e_devolve_sucesso(capsys):
    @contextmanager
    def open_session():
        yield FakeSession()

    assert run(open_session) == 0
    assert "200 artigos, 10 análises" in capsys.readouterr().out


def test_falha_devolve_codigo_1_sem_vazar_a_mensagem(capsys):
    class DatabaseDown(Exception):
        pass

    @contextmanager
    def open_session():
        raise DatabaseDown("host secreto db.abc.supabase.co")
        yield

    assert run(open_session) == 1
    captured = capsys.readouterr()
    assert "DatabaseDown" in captured.err
    assert "secreto" not in captured.err and "secreto" not in captured.out