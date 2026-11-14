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



def test_dicas_de_formato_para_url_valida_nao_apontam_problema():
    from scripts.keepalive import url_format_hints

    assert url_format_hints("postgresql://postgres.abc:senha@aws-0-x.pooler.supabase.com:5432/postgres") == []


def test_dicas_apontam_aspas_prefixo_espaco_e_arrobas_sem_vazar_o_valor():
    from scripts.keepalive import url_format_hints

    hints = url_format_hints('"DATABASE_URL=postgresql://u:SEGREDOX@@servidor/db"\n')
    text = " ".join(hints)
    assert "aspas" in text and "quebra de linha" in text and "DATABASE_URL=" in text
    assert "2 sinais" in text
    assert "SEGREDOX" not in text and "servidor" not in text  # nada do conteúdo aparece nas dicas


def test_dica_para_variavel_vazia_e_para_esquema_errado():
    from scripts.keepalive import url_format_hints

    assert "vazia" in url_format_hints("")[0]
    assert any("postgresql://" in h for h in url_format_hints("mysql://u:p@h/db"))


def test_main_nao_vaza_o_conteudo_quando_o_banco_nao_configura(monkeypatch, capsys):
    import sys

    from scripts import keepalive

    monkeypatch.setitem(sys.modules, "app.core.database", None)  # a importação falha
    monkeypatch.setenv("DATABASE_URL", "'postgresql://u:SEGREDO@host/db'")
    assert keepalive.main() == 1
    err = capsys.readouterr().err
    assert "Falha ao configurar o banco" in err and "aspas" in err
    assert "SEGREDO" not in err and "host" not in err