from pathlib import Path
import json
import pytest
from fastapi.testclient import TestClient
from app import runtime
from app.persistence.settings import PersistenceSettings,PROJECT_ROOT


def test_dotenv_is_loaded_without_cwd_dependency(tmp_path,monkeypatch):
    monkeypatch.delenv('SA_DATABASE_URL',raising=False)
    env=tmp_path/'local.env'
    env.write_text('SA_DATABASE_URL=postgresql+psycopg://example:only-a-test@localhost:5432/test_db\nSA_MAXIMUM_UPLOAD_BYTES=4096\n')
    other=tmp_path/'other';other.mkdir();monkeypatch.chdir(other)
    settings=PersistenceSettings(_env_file=env)
    assert settings.database_url.get_secret_value().endswith('/test_db') and settings.maximum_upload_bytes==4096
    assert 'only-a-test' not in repr(settings)
    assert PersistenceSettings.model_config['env_file']==PROJECT_ROOT/'.env'


def test_environment_overrides_dotenv(tmp_path,monkeypatch):
    env=tmp_path/'config.env';env.write_text('SA_DATABASE_URL=postgresql://u:sample@localhost/file_db\n')
    monkeypatch.setenv('SA_DATABASE_URL','postgresql://u:sample@localhost/environment_db')
    assert PersistenceSettings(_env_file=env).database_url.get_secret_value().endswith('/environment_db')


def test_unconfigured_is_not_an_application_failure():
    def forbidden(*args,**kwargs):raise AssertionError('An unconfigured check must not connect.')
    result=runtime.inspect_runtime(PersistenceSettings(database_url=None,_env_file=None),engine_factory=forbidden)
    assert result.status=='UNCONFIGURED' and result.ui_available and not result.ready
    assert result.database_reachable is None and result.migrations_current is None
    assert 'Failed' not in result.message


def test_invalid_configuration_does_not_expose_input(monkeypatch):
    monkeypatch.setenv('SA_DATABASE_URL','malformed-sensitive-password')
    result=runtime.inspect_runtime()
    assert result.status=='INVALID_CONFIGURATION'
    assert 'sensitive' not in json.dumps(result.payload())


def test_unreachable_redacts_exception_and_url():
    password='do-not-display-test-secret'
    settings=PersistenceSettings(database_url=f'postgresql://u:{password}@localhost/test',_env_file=None)
    def failing(*args,**kwargs):raise RuntimeError(settings.database_url.get_secret_value())
    result=runtime.inspect_runtime(settings,engine_factory=failing)
    payload=result.payload()
    assert payload['status']=='DATABASE_UNAVAILABLE' and payload['database_configured'] is True
    assert payload['database_reachable'] is False and payload['migrations_current'] is None
    assert password not in json.dumps(payload) and 'postgresql://' not in json.dumps(payload)


def test_startup_and_documentation_routes(monkeypatch):
    from app.main import app
    state=runtime.RuntimeStatus('UNCONFIGURED','Controlled setup required',False)
    monkeypatch.setattr(runtime,'inspect_runtime',lambda:state)
    with TestClient(app) as client:
        assert app.state.runtime_status==state
        assert client.get('/api/runtime').json()['status']=='UNCONFIGURED'
        assert client.get('/api/runtime?refresh=true').json()['ui_available'] is True
        assert client.get('/api/health').json()['status']=='healthy'
        assert client.get('/docs').status_code==200
        assert client.get('/redoc').status_code==200
        assert client.get('/openapi.json').json()['openapi']
        assert client.get('/ui/').status_code==200
        legacy=client.get('/ui/docs',follow_redirects=False)
        assert legacy.status_code in (307,308) and legacy.headers['location']=='/docs'
        assert client.get('/ui/docs').status_code==200
        setup=client.get('/setup')
        assert setup.status_code==200 and 'alembic upgrade head' in setup.text
        assert 'href="/docs"' in setup.text and 'href="/ui/docs"' not in setup.text



def test_runtime_empty_loading_and_navigation_scenario():
    import subprocess,sys
    result=subprocess.run([sys.executable,'-m','tests.ui_runtime_scenario'],cwd=PROJECT_ROOT,capture_output=True,text=True,timeout=60)
    assert result.returncode==0,result.stdout+'\n'+result.stderr
    assert 'RUNTIME_UI_SCENARIO_PASSED' in result.stdout
    assert 'Traceback (most recent call last)' not in result.stderr,result.stderr


@pytest.mark.parametrize('pair',['subtitle','pass','warning','fail','nav'])
def test_authored_palette_text_contrast(pair):
    # WCAG 2.2 relative luminance; tests authored colors, not rendered conformance.
    import ast,re
    css=(PROJECT_ROOT/'app/ui/styles.css').read_text()
    source=ast.parse((PROJECT_ROOT/'app/ui/pages.py').read_text())
    colors=next({k.arg:ast.literal_eval(k.value) for k in node.keywords} for node in ast.walk(source)
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr=='colors')
    subtitle=re.search(r'\.sa-subtitle\s*\{[^}]*color:(#[0-9a-f]+)',css).group(1)
    pairs={'subtitle':(subtitle,'#f3f6fa'),'pass':('#ffffff',colors['positive']),
        'warning':('#ffffff',colors['warning']),'fail':('#ffffff',colors['negative']),'nav':('#c5d3e4','#11243b')}
    def luminance(h):
        rgb=[int(h[i:i+2],16)/255 for i in (1,3,5)]
        linear=[x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4 for x in rgb]
        return sum(a*b for a,b in zip(linear,(.2126,.7152,.0722)))
    high,low=sorted((luminance(h) for h in pairs[pair]),reverse=True)
    assert (high+.05)/(low+.05)>=4.5



def test_bare_postgresql_url_uses_psycopg3_for_diagnostics():
    seen=[]
    def factory(url,**kwargs):
        seen.append((url.drivername,kwargs['connect_args']['connect_timeout']))
        raise RuntimeError('Controlled diagnostic connection failure')
    result=runtime.inspect_runtime(PersistenceSettings(database_url='postgresql://u:sample@localhost/db',_env_file=None),engine_factory=factory)
    assert seen==[('postgresql+psycopg',3)]
    assert result.status=='DATABASE_UNAVAILABLE'


def test_mounted_ui_favicon_is_served_without_runtime_error(monkeypatch):
    from app.main import app
    state=runtime.RuntimeStatus('READY','Controlled database ready',True,True,True)
    monkeypatch.setattr(runtime,'inspect_runtime',lambda:state)
    with TestClient(app,raise_server_exceptions=False) as client:
        response=client.get('/ui/favicon.ico')
        assert response.status_code==200
        assert response.headers['content-type'].startswith('image/')
        assert response.content.startswith(b'\x00\x00\x01\x00')
