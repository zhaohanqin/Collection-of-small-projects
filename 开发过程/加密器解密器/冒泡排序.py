def bubble_sort(arr):
    """
    冒泡排序算法实现（优化版）
    
    参数:
        arr (list): 待排序的整数列表
        
    返回:
        list: 排序后的整数列表
    """
    n = len(arr)
    
    # 外层循环控制排序轮数
    for i in range(n):
        # 优化标志：记录当前轮是否发生交换
        swapped = False
        
        # 内层循环进行相邻元素比较（每轮减少i个已排序元素）
        for j in range(0, n - i - 1):
            # 如果前一个元素大于后一个，交换位置
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
                swapped = True
                print(f"第{i+1}轮，第{j+1}次交换：{arr}")
        
        # 如果本轮没有发生交换，说明已经有序，提前终止
        if not swapped:
            break
    
    return arr

# 示例用法
if __name__ == "__main__":
    test_array = [64, 34, 25, 12, 22, 11, 90]
    print("排序前:", test_array)
    sorted_array = bubble_sort(test_array)
    # print("排序前:", test_array)  # 注意：原列表会被修改，这里打印的是排序后的结果
    print("排序后:", sorted_array)
