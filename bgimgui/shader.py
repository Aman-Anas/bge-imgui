from bgl import *


class ShaderProgram:
    def __init__(self):
        self.valid = False

    def attachShader(self, shaderCode):
        if not self.valid:
            self.validate()

        glAttachShader(self.programId, shaderCode.getShaderId())
        glLinkProgram(self.programId)

    def bind(self):
        if not self.valid:
            self.validate()
        glUseProgram(self.programId)

    def release(self):
        if not self.valid:
            self.validate()
        glUseProgram(0)

    def validate(self):
        self.programId = glCreateProgram()
        self.valid = True


class ShaderCode:
    def __init__(self, shaderType, code):
        self.shaderType = shaderType
        self.code = code
        self.valid = False

        # read in a file if needs be
        if type(code) == type(''):  # assume it's a file
            file = open(code, 'r')
            self.code = [line for line in file.readlines()]

    def getShaderId(self):  # must be called in OpenGL context
        if not self.valid:
            self.validate()
        return self.shaderId

    def validate(self):  # must be called in OpenGL context
        self.shaderId = glCreateShader(self.shaderType)
        glShaderSource(self.shaderId, self.code)
        glCompileShader(self.shaderId)

        status = glGetShaderiv(self.shaderId, GL_COMPILE_STATUS)

        if not status:
            if glGetShaderiv(self.shaderId, GL_INFO_LOG_LENGTH) != 0:
                errorLines = glGetShaderInfoLog(self.shaderId)
                sys.stderr.write(errorLines)
            glDeleteShader(shader)
            raise ValueError('Shader compilation failed')

        self.valid = True
