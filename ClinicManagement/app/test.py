a = [1,2]
b = [[2, 4, 6, 8], [5, 6]]
for i in range(len(a)):
    print(a[i], end=" ")
    for j in range(len(b[i])):
        print(b[i][j], end=" ")
    print()