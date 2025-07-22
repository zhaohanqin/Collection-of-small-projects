# 加密解密器是一个简单的加密解密工具，可以对文本进行加解密操作。
# 加密算法使用的是字符的Unicode码的加减法，解密算法则是使用相同的算法，但将偏移量取反。
# 加密解密器的使用方法很简单，只需要输入模式（加密或解密）、文本、偏移量（默认为3），然后点击运行即可。
# 加密解密器的加密解密算法可以自行修改，只需修改encrypt()和decrypt()函数即可。
# 保留原有的加密解密函数
def encrypt(text: str, shift: int = 3) -> str:
    """加密函数：将每个字符的Unicode码增加指定数值"""
    return ''.join([chr(ord(c) + shift) for c in text])


def decrypt(text: str, shift: int = 3) -> str:
    """解密函数：将每个字符的Unicode码减少指定数值"""
    return ''.join([chr(ord(c) - shift) for c in text])


if __name__ == "__main__":

    # 用户交互界面
    print("欢迎使用加密解密器")

    # 获取用户输入
    mode = input("请选择模式 [加密/解密]: ").strip()
    text = input("请输入文本: ").strip()
    shift = int(input("请输入偏移量 (默认3): ") or 3)

    # 执行加解密操作
    if mode == "加密":
        result = encrypt(text, shift)
        print(f"加密结果: {result}")
    elif mode == "解密":
        result = decrypt(text, shift)
        print(f"解密结果: {result}")
    else:
        print("无效模式，请输入'加密'或'解密'")
