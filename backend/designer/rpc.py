"""Bounded local gRPC calls using the installed API's own service descriptors."""
import importlib


class DesignerRPC:
    def __init__(self, port=50051, timeout=10):
        try:
            self.grpc = importlib.import_module("grpc")
            reflection = importlib.import_module("grpc_reflection.v1alpha.reflection_pb2")
            stubs = importlib.import_module("grpc_reflection.v1alpha.reflection_pb2_grpc")
            descriptors = importlib.import_module("google.protobuf.descriptor_pool")
            self.factory = importlib.import_module("google.protobuf.message_factory")
            self.json = importlib.import_module("google.protobuf.json_format")
        except ImportError as error:
            raise RuntimeError('Install the Designer dependencies: python -m pip install -e ".[designer]"') from error
        self.timeout, self.reflection = timeout, reflection
        self.channel = self.grpc.insecure_channel(f"127.0.0.1:{port}")
        self.stub = stubs.ServerReflectionStub(self.channel)
        self.pool = descriptors.DescriptorPool()

    def describe(self, service):
        try:
            return self.pool.FindServiceByName(service)
        except KeyError:
            request = self.reflection.ServerReflectionRequest(file_containing_symbol=service)
            replies = self.stub.ServerReflectionInfo(iter([request]), timeout=self.timeout)
            pending = [raw for reply in replies for raw in reply.file_descriptor_response.file_descriptor_proto]
            while pending:
                remaining = []
                for raw in pending:
                    try:
                        self.pool.AddSerializedFile(raw)
                    except TypeError:
                        remaining.append(raw)
                if len(remaining) == len(pending):
                    raise RuntimeError("TD Designer returned unresolved API descriptor dependencies.")
                pending = remaining
            return self.pool.FindServiceByName(service)

    def call(self, service, method, values=None, timeout=None):
        descriptor = self.describe(service).FindMethodByName(method)
        request = self.factory.GetMessageClass(descriptor.input_type)()
        self.json.ParseDict(values or {}, request)
        response = self.factory.GetMessageClass(descriptor.output_type)
        invoke = self.channel.unary_unary("/" + service + "/" + method,
                    request_serializer=request.SerializeToString, response_deserializer=response.FromString)
        return self.json.MessageToDict(invoke(request, timeout=timeout or self.timeout))

    def script(self, path, timeout=30):
        result = self.call("ansys.api.dbu.v0.dbuapplication.DbuApplication", "RunScriptFile",
                           {"script_path": str(path), "api_version": 261}, timeout)
        if not result.get("success"):
            raise RuntimeError("TD Designer script failed: " + result.get("message", "no details"))
        return result

    def close(self):
        self.channel.close()
