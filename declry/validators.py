# _*_  encoding: utf-8 _*_

from django.core.exceptions import ValidationError
import re

def ps(l1,l2):
	return sum(map(lambda x,y:int(x)*y,l1,l2))

def validate_nif(val):
	w = (9,8,7,6,5,4,3,2,0)
	try:
		if len(val) != 9: raise
		if val[0] == '0': raise
		dig = 11 - ps(val,w) % 11
		if dig>9: dig = 0
		if int(val[-1]) != dig: raise
	except:
		raise ValidationError('NIF (Número de identificação fiscal) Inválido')


def validate_ncc(val):
	try:
		if len(val) != 12 : raise
		l = [int(x,36) for x in val]
		t = 0
		for i,x in enumerate(l):
			if i % 2 ==0:
				x *= 2
				if x>= 10: x-=9
			t += x	
		if (t % 10) != 0: raise	
	except:
		raise ValidationError('Número do cartão de cidadão inválido')


def validate_niss(val):
	w = (29,23,19,17,13,11,7,5,3,2,0)
	try:
		if len(val) != 11 : raise
		if val[0] not in "12" : raise
		if int(val[-1]) != (9 - ps(val,w) % 10): raise
	except:
		raise ValidationError('NISS (Número de identificação da segurança social) inválido')


def validate_nib(val):
	w = (73,17,89,38,62,45,53,15,50,5,49,34,81,76,27,90,9,30,3,0,0)
	try:
		if len(val) != 21 : raise
		if int(val[-2:]) != (98 - ps(val,w) % 97): raise
	except:
		raise ValidationError('NIB (Número de identificação bancária) inválido')


def validate_iban(val):
	try:
		if not (21<= len(val) <= 34) : raise
		val=val[4:]+''.join([str(int(c,36)) for c in val[:4]])
		if long(val) % 97 != 1: raise
	except:
		raise ValidationError('IBAN (Número de identificação bancária internacional) inválido')


def validate_isbn10(val):
	w=(10,9,8,7,6,5,4,3,2,1)
	val= [int(x) if x!='X' else 10 for x in val]  #if x in string.digits or x in ('x','X')
	if sum(map(lambda x,y: x*y, val,w)) % 11 != 0: raise


def validate_isbn13(val):
	w=(1,3,1,3,1,3,1,3,1,3,1,3,0)
	try:
		val= [int(x) if x!='X' else 10 for x in val]  
		if (10 - sum(map(lambda x,y: x*y, val,w) % 10) % 10)!= val[-1]: raise
	except:
		raise ValidationError('Número de ISBN13 inválido')


def validate_tel(val):
	if not re.match(r'00[0-9]*$|\+[0-9]*$|2[0-9]{8}$|9[1236][0-9]{7}$',val):
		raise ValidationError('Número de telefone inválido')

def validate_tels(val):
	map(validate_tel, val.split())
	

def validate_any(*args, **kwargs):
	"validates if any of the args is not none else raises validation error with error_msg"
	if not any(args):
		raise ValidationError(kwargs.get('error_msg','Error'))

def validate_just_one(*args, **kwargs):
	"validates if just one of the args is not none else raises validation error with error_msg"
	if len([x for x in args if x]) !=1:
		raise ValidationError(kwargs.get('error_msg','Error'))
