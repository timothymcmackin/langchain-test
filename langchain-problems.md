https://docs.langchain.com/oss/python/langgraph/local-server#2-create-a-langgraph-app

- got this error:

```
❯ langgraph new langgraph-app --template new-langgraph-project-python
📥 Attempting to download repository as a ZIP archive...
URL: https://github.com/langchain-ai/new-langgraph-project/archive/refs/heads/main.zip
Traceback (most recent call last):
  File "/Library/Frameworks/Python.framework/Versions/3.14/lib/python3.14/urllib/request.py", line 1321, in do_open
    h.request(req.get_method(), req.selector, req.data, headers,
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
              encode_chunked=req.has_header('Transfer-encoding'))
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Library/Frameworks/Python.framework/Versions/3.14/lib/python3.14/http/client.py", line 1367, in request
    self._send_request(method, url, body, headers, encode_chunked)
    ~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Library/Frameworks/Python.framework/Versions/3.14/lib/python3.14/http/client.py", line 1413, in _send_request
    self.endheaders(body, encode_chunked=encode_chunked)
    ~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Library/Frameworks/Python.framework/Versions/3.14/lib/python3.14/http/client.py", line 1362, in endheaders
    self._send_output(message_body, encode_chunked=encode_chunked)
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Library/Frameworks/Python.framework/Versions/3.14/lib/python3.14/http/client.py", line 1122, in _send_output
    self.send(msg)
    ~~~~~~~~~^^^^^
  File "/Library/Frameworks/Python.framework/Versions/3.14/lib/python3.14/http/client.py", line 1066, in send
    self.connect()
    ~~~~~~~~~~~~^^
  File "/Library/Frameworks/Python.framework/Versions/3.14/lib/python3.14/http/client.py", line 1508, in connect
    self.sock = self._context.wrap_socket(self.sock,
                ~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^
                                          server_hostname=server_hostname)
                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Library/Frameworks/Python.framework/Versions/3.14/lib/python3.14/ssl.py", line 455, in wrap_socket
    return self.sslsocket_class._create(
           ~~~~~~~~~~~~~~~~~~~~~~~~~~~~^
        sock=sock,
        ^^^^^^^^^^
    ...<5 lines>...
        session=session
        ^^^^^^^^^^^^^^^
    )
    ^
  File "/Library/Frameworks/Python.framework/Versions/3.14/lib/python3.14/ssl.py", line 1076, in _create
    self.do_handshake()
    ~~~~~~~~~~~~~~~~~^^
  File "/Library/Frameworks/Python.framework/Versions/3.14/lib/python3.14/ssl.py", line 1372, in do_handshake
    self._sslobj.do_handshake()
    ~~~~~~~~~~~~~~~~~~~~~~~~~^^
ssl.SSLCertVerificationError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1082)

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/Users/tim/repos/langchain-test/.venv/bin/langgraph", line 6, in <module>
    sys.exit(cli())
             ~~~^^
  File "/Users/tim/repos/langchain-test/.venv/lib/python3.14/site-packages/click/core.py", line 1569, in __call__
    return self.main(*args, **kwargs)
           ~~~~~~~~~^^^^^^^^^^^^^^^^^
  File "/Users/tim/repos/langchain-test/.venv/lib/python3.14/site-packages/click/core.py", line 1490, in main
    rv = self.invoke(ctx)
  File "/Users/tim/repos/langchain-test/.venv/lib/python3.14/site-packages/click/core.py", line 1970, in invoke
    return _process_result(sub_ctx.command.invoke(sub_ctx))
                           ~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^
  File "/Users/tim/repos/langchain-test/.venv/lib/python3.14/site-packages/click/core.py", line 1353, in invoke
    return ctx.invoke(self.callback, **ctx.params)
           ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/tim/repos/langchain-test/.venv/lib/python3.14/site-packages/click/core.py", line 907, in invoke
    return callback(*args, **kwargs)
  File "/Users/tim/repos/langchain-test/.venv/lib/python3.14/site-packages/langgraph_cli/analytics.py", line 103, in decorator
    return func(*args, **kwargs)
  File "/Users/tim/repos/langchain-test/.venv/lib/python3.14/site-packages/langgraph_cli/cli.py", line 922, in new
    return create_new(path, template)
  File "/Users/tim/repos/langchain-test/.venv/lib/python3.14/site-packages/langgraph_cli/templates.py", line 184, in create_new
    _download_repo_with_requests(template_url, path)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/Users/tim/repos/langchain-test/.venv/lib/python3.14/site-packages/langgraph_cli/templates.py", line 104, in _download_repo_with_requests
    with request.urlopen(repo_url) as response:
         ~~~~~~~~~~~~~~~^^^^^^^^^^
  File "/Library/Frameworks/Python.framework/Versions/3.14/lib/python3.14/urllib/request.py", line 187, in urlopen
    return opener.open(url, data, timeout)
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/Library/Frameworks/Python.framework/Versions/3.14/lib/python3.14/urllib/request.py", line 487, in open
    response = self._open(req, data)
  File "/Library/Frameworks/Python.framework/Versions/3.14/lib/python3.14/urllib/request.py", line 504, in _open
    result = self._call_chain(self.handle_open, protocol, protocol +
                              '_open', req)
  File "/Library/Frameworks/Python.framework/Versions/3.14/lib/python3.14/urllib/request.py", line 464, in _call_chain
    result = func(*args)
  File "/Library/Frameworks/Python.framework/Versions/3.14/lib/python3.14/urllib/request.py", line 1369, in https_open
    return self.do_open(http.client.HTTPSConnection, req,
           ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                        context=self._context)
                        ^^^^^^^^^^^^^^^^^^^^^^
  File "/Library/Frameworks/Python.framework/Versions/3.14/lib/python3.14/urllib/request.py", line 1324, in do_open
    raise URLError(err)
urllib.error.URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1082)>
```



https://docs.langchain.com/oss/python/langgraph/local-server#7-test-the-api

How do I know if this worked? Expected output?



https://docs.langchain.com/oss/python/langgraph/thinking-in-langgraph#testing-the-agent

could not complete; code in thinking_in but maybe I didn't copy something or it's supposed to be in a different file?

Claude had to do several things including installing dependencies to get this to work.



https://docs.langchain.com/oss/python/deepagents/rag#select-an-embeddings-model

- example uses `OllamaEmbeddings(model="llama3")` — llama3 is a chat model, not an embedding model
- got this error:

ollama._types.ResponseError: This server does not support embeddings. Start it with `--embeddings` (status code: 501)

- fix: `ollama pull nomic-embed-text`, then `OllamaEmbeddings(model="nomic-embed-text")`





## Need to qualify what things are

Once we’ve instantiated a VectorStore that contains documents, we can query it. VectorStore includes methods for querying:

https://docs.langchain.com/oss/python/langchain/knowledge-base#seeding-the-vector-store

What's a vectorstore? could be a lot of things based on the context

