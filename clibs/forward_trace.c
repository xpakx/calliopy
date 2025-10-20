#include <stdio.h>
#include <stdarg.h>
#include <string.h>


typedef void (*TraceLogCallback)(int, const char *, va_list);
void SetTraceLogCallback(TraceLogCallback callback); 

typedef void (*PyTraceCallback)(int level, const char *msg);

static PyTraceCallback g_py_callback = NULL;

static void ForwardTrace(int level, const char *text, va_list args)
{
    if (!g_py_callback) return;

    char buffer[1024];
    vsnprintf(buffer, sizeof(buffer), text, args);
    g_py_callback(level, buffer);
}

void SetPythonTraceCallback(PyTraceCallback cb)
{
    g_py_callback = cb;
    SetTraceLogCallback(ForwardTrace);
}
