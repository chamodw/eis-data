def getProgressBar (i, n):
	i = i+1
	fill = '█'
	l = 80
	blank = '-'
	f = int(i*l/n)
	e = 80-int(i*l/n)
	print (f, e)
	p = fill*f + blank*e + '|' + " " + str(i) + "/" + str(n)
	
	return p


n = 3
for i in range(n):
	print (getProgressBar(i, n))
