
import re
from datetime import datetime, timedelta
import calendar

CIRCA = 5 # years
CIRCA_D = timedelta(days=365*CIRCA)

share_re = re.compile("([0-9]+)/([0-9]+)")

def share_parse(value):
	if value is None:
		return None
	else:
		m = share_re.match(value)
		if m:
			(t,b) = m.groups()
			return float(t) / float(b)
		else:
			print("Could not parse raw share: %s" % value)
			return None

def ymd_to_datetime(year, month, day, which="begin"):


	if not isinstance(year, int):
		try:
			year = int(year)
		except:
			print("DATE CLEAN: year is %r; returning None" % year)
			return None

	if not isinstance(month, int):
		try:
			month = int(month)
		except:
			print("DATE CLEAN: month is %r; continuing with %s" % (month, "earliest" if which=="begin" else "latest"))
			month = None

	if not isinstance(day, int):
		try:
			day = int(day)
		except:
			day = None

	if not month or month > 12 or month < 1:
		if which == "begin":
			month = 1
		else:
			month = 12

	maxday = calendar.monthrange(year, month)[1]
	if not day or day > maxday or day < 1:
		if which == "begin":
			day = 1
		else:
			# number of days in month
			day = maxday

	ystr = "%04d" % abs(year)
	if year < 0:
		ystr = "-" + ystr

	if which == "begin":
		return "%s-%02d-%02dT00:00:00" % (ystr, month, day)
	else:
		return "%s-%02d-%02dT23:59:59" % (ystr, month, day)



def date_parse(value, delim):
	# parse a / or - or . date or range

	bits = value.split(delim)
	if len(bits) == 2:
		# YYYY/ range
		b1 = bits[0].strip()
		b2 = bits[1].strip()
		if len(b2) < 3 :
			b2 = "%s%s" % (b1[:len(b2)], b2)
		elif len(b2) > 4:
			print("Bad range: %s" % value)
			return None
		try:
			return [datetime(int(b1),1,1), datetime(int(b2)+1,1,1)]
		except:
			print("Broken delim: %s" % value)
			return None
	elif len(bits) == 3:
		# YYYY/MM/DD or YY/YY/YYYY or DD.MM.YYYY or YYYY.MM.DD
		m = int(bits[1])
		if len(bits[0]) == 4:
			y = int(bits[0])
			d = int(bits[2])
		else:
			y = int(bits[2])
			d = int(bits[0])
		if m == 0:
			m = 1
		if d == 0:
			d = 1
		if m > 12:
			# swap them
			d, m = m, d
		try:
			return [datetime(y,m,d), datetime(y,m,d)]
		except:
			print("Bad // value: %s" % value)
	else:
		print("broken / date: %s" % value)
	return None




def date_cleaner(value):

	# FORMATS:

	# YYYY[?]
	# YYYY/MM/DD
	# DD/MM/YYYY
	# ca. YYYY
	# aft[er|.] YYYY
	# bef[ore|.] YYYY
	# YYYY.MM.DD
	# YYYY/(Y|YY|YYYY)
	# YYYY-YY
	# YYY0s

	if value:
		value = value.replace("?",'')
		value = value.replace('est', '')
		value = value.replace("()", '')
		value = value.replace(' or ', '/')
		value = value.strip()
		value = value.replace('by ', 'bef.')
		value = value.replace('c.', 'ca.')
		value = value.replace('CA.', 'ca.')
		value = value.replace('af.', 'aft.')

	if not value:
		return value
	elif value.startswith("|"):
		# Broken? null it out
		return None
	elif len(value) == 4 and value.isdigit():
		# year only
		return [datetime(int(value),1,1), datetime(int(value)+1,1,1)]

	elif value.startswith('v.'):
		value = value[2:].strip()
		return None

	elif value.endswith('s'):
		# 1950s
		if len(value) == 5 and value[:4].isdigit():
			y = int(value[:4])
			return [datetime(y,1,1), datetime(y+10,1,1)]
		else:
			print("Bad YYYYs date: %s" % value)
			return None
	elif value.startswith("ca"):
		# circa x
		value = value[3:].strip()
		if len(value) == 4 and value.isdigit():
			y = int(value)
			return [datetime(y-CIRCA,1,1), datetime(y+CIRCA,1,1)]
		else:
			# Try and parse it
			if value.find('/') > -1:
				val = date_parse(value, '/')
			elif value.find('-') > -1:
				val = date_parse(value, '-')
			else:
				print("bad circa: %s" % value)
				return None

			val[0] -= CIRCA_D
			val[1] += CIRCA_D
			return val
	elif value.startswith('aft'):
		# after x
		value = value.replace('aft.', '')
		value = value.replace('after ', '')
		value = value.strip()
		try:
			y = int(value)
		except:
			print("Bad aft value: %s" % value)
			return None
		return [datetime(y,1,1), None]
	elif value.startswith('bef'):
		value = value.replace('bef.', '')
		value = value.replace('before ', '')
		value = value.strip()
		y = int(value)
		return [None, datetime(y,1,1)]
	elif value.find('/') > -1:
		# year/year or year/month/date
		# 1885/90
		# 07/02/1897
		return date_parse(value, '/')
	elif value.find('.') > -1:
		return date_parse(value, '.')
	elif value.find('-') > -1:
		return date_parse(value, '-')
	elif value.find(';') > -1:
		return date_parse(value, ';')

	else:
		print("fell through to: %s" % value)
		return value



def test_date_cleaner():
	import sqlite3
	c = sqlite3.connect('/Users/rsanderson/Development/getty/provenance/matt/gpi.sqlite')
	res = c.execute("SELECT DISTINCT person_birth_date from gpi_people")
	x = 0
	for d in res:
		date_cleaner(d[0])
		x += 1
	res = c.execute("SELECT DISTINCT person_death_date from gpi_people")
	for d in res:
		date_cleaner(d[0])
		x += 1

	print("Tried %s dates" % x)

def test_share_parser():
	import sqlite3
	c = sqlite3.connect('/Users/rsanderson/Development/getty/pipeline/data/raw_gpi.sqlite')
	res = c.execute("SELECT DISTINCT joint_own_sh_1 FROM raw_knoedler")
	x = 0
	for s in res:
		x += 1
		# print(share_parse(s[0]))
	res = c.execute("SELECT DISTINCT joint_own_sh_2 FROM raw_knoedler")
	for s in res:
		x += 1
		# print(share_parse(s[0]))
	print("Tried %s shares" % x)

if __name__ == "__main__":
	# test_date_cleaner()
	test_share_parser()
