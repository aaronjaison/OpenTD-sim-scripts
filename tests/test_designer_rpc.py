"""Reflection dependency ordering, bounded RPCs and helpful optional-install errors."""
from types import SimpleNamespace as S
from unittest.mock import Mock
import pytest
from backend.designer import rpc


def client(monkeypatch):
    channel=Mock();pool=Mock();stub=Mock();factory=Mock();fmt=Mock()
    modules={'grpc':S(insecure_channel=Mock(return_value=channel)),
             'grpc_reflection.v1alpha.reflection_pb2':S(ServerReflectionRequest=Mock()),
             'grpc_reflection.v1alpha.reflection_pb2_grpc':S(ServerReflectionStub=Mock(return_value=stub)),
             'google.protobuf.descriptor_pool':S(DescriptorPool=Mock(return_value=pool)),
             'google.protobuf.message_factory':factory,'google.protobuf.json_format':fmt}
    monkeypatch.setattr(rpc.importlib,'import_module',lambda n:modules[n])
    return rpc.DesignerRPC(),channel,pool,stub,factory,fmt


def test_dependency_missing(monkeypatch):
    monkeypatch.setattr(rpc.importlib,'import_module',Mock(side_effect=ImportError('missing')))
    with pytest.raises(RuntimeError,match='designer'):rpc.DesignerRPC()


def test_reflection(monkeypatch):
    c,channel,pool,stub,factory,fmt=client(monkeypatch)
    service=Mock();pool.FindServiceByName.side_effect=[KeyError(),service]
    stub.ServerReflectionInfo.return_value=[S(file_descriptor_response=S(file_descriptor_proto=[b'dependent',b'base']))]
    pool.AddSerializedFile.side_effect=[TypeError(),None,None]
    assert c.describe('service') is service
    assert pool.AddSerializedFile.call_count==3
    assert stub.ServerReflectionInfo.call_args.kwargs['timeout']==10
    pool.FindServiceByName.side_effect=KeyError()
    pool.AddSerializedFile.side_effect=TypeError()
    with pytest.raises(RuntimeError,match='dependencies'):c.describe('service')


def test_call_and_script(monkeypatch):
    c,channel,pool,stub,factory,fmt=client(monkeypatch)
    fmt.MessageToDict.return_value={'success':True}
    assert c.call('service','method')=={'success':True}
    assert channel.unary_unary.return_value.call_args.kwargs['timeout']==10
    assert c.script('file.py',44)['success']
    assert channel.unary_unary.return_value.call_args.kwargs['timeout']==44
    fmt.MessageToDict.return_value={'message':'invalid command'}
    with pytest.raises(RuntimeError,match='invalid command'):c.script('file.py')
    fmt.MessageToDict.return_value={}
    with pytest.raises(RuntimeError,match='no details'):c.script('file.py')
    c.close();channel.close.assert_called_once()
