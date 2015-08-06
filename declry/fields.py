# _*_  encoding: utf-8 _*_

from django.utils.translation import ugettext as _
from django.db import models
from django.forms import fields
from validators import validate_tels, validate_nib, validate_nif, validate_niss, validate_iban
#import autocomplete_light
from decimal import Decimal


# ISO 3166-1 
COUNTRIES = (
	('PT', 'Portugal'),
	('ZA', 'África do Sul'),
	('AX', 'Åland, Ilhas'),
	('AL', 'Albânia'),
	('DE', 'Alemanha'),
	('AD', 'Andorra'),
	('AO', 'Angola'),
	('AI', 'Anguilla'),
	('AQ', 'Antárctida'),
	('AG', 'Antigua e Barbuda'),
	('AN', 'Antilhas Holandesas'),
	('SA', 'Arábia Saudita'),
	('DZ', 'Argélia'),
	('AR', 'Argentina'),
	('AM', 'Arménia'),
	('AW', 'Aruba'),
	('AU', 'Austrália'),
	('AT', 'Áustria'),
	('AZ', 'Azerbeijão'),
	('BS', 'Bahamas'),
	('BH', 'Bahrain'),
	('BD', 'Bangladesh'),
	('BB', 'Barbados'),
	('BE', 'Bélgica'),
	('BZ', 'Belize'),
	('BJ', 'Benin'),
	('BM', 'Bermuda'),
	('BY', 'Bielo-Rússia'),
	('BO', 'Bolívia'),
	('BA', 'Bósnia-Herzegovina'),
	('BW', 'Botswana'),
	('BV', 'Bouvet, Ilha'),
	('BR', 'Brasil'),
	('BN', 'Brunei'),
	('BG', 'Bulgária'),
	('BF', 'Burkina Faso'),
	('BI', 'Burundi'),
	('BT', 'Butão'),
	('CV', 'Cabo Verde'),
	('KH', 'Cambodja'),
	('CM', 'Camarões'),
	('CA', 'Canadá'),
	('KY', 'Cayman, Ilhas'),
	('KZ', 'Cazaquistão'),
	('CF', 'Centro-africana, República'),
	('TD', 'Chade'),
	('CZ', 'Checa, República'),
	('CL', 'Chile'),
	('CN', 'China'),
	('CY', 'Chipre'),
	('CX', 'Christmas, Ilha'),
	('CC', 'Cocos, Ilhas'),
	('CO', 'Colômbia'),
	('KM', 'Comores'),
	('CG', 'Congo'),
	('CD', 'Congo, República Democrática do (antigo Zaire)'),
	('CK', 'Cook, Ilhas'),
	('KR', 'Coreia do Sul'),
	('KP', 'Coreia, República Democrática da (Coreia do Norte)'),
	('CI', 'Costa do Marfim'),
	('CR', 'Costa Rica'),
	('HR', 'Croácia'),
	('CU', 'Cuba'),
	('DK', 'Dinamarca'),
	('DJ', 'Djibouti'),
	('DM', 'Dominica'),
	('DO', 'Dominicana, República'),
	('EG', 'Egipto'),
	('SV', 'El Salvador'),
	('AE', 'Emiratos Árabes Unidos'),
	('EC', 'Equador'),
	('ER', 'Eritreia'),
	('SK', 'Eslováquia'),
	('SI', 'Eslovénia'),
	('ES', 'Espanha'),
	('US', 'Estados Unidos da América'),
	('EE', 'Estónia'),
	('ET', 'Etiópia'),
	('FO', 'Faroe, Ilhas'),
	('FJ', 'Fiji'),
	('PH', 'Filipinas'),
	('FI', 'Finlândia'),
	('FR', 'França'),
	('GA', 'Gabão'),
	('GM', 'Gâmbia'),
	('GH', 'Gana'),
	('GE', 'Geórgia'),
	('GS', 'Geórgia do Sul e Sandwich do Sul, Ilhas'),
	('GI', 'Gibraltar'),
	('GR', 'Grécia'),
	('GD', 'Grenada'),
	('GL', 'Gronelândia'),
	('GP', 'Guadalupe'),
	('GU', 'Guam'),
	('GT', 'Guatemala'),
	('GY', 'Guiana'),
	('GF', 'Guiana Francesa'),
	('GW', 'Guiné-Bissau'),
	('GN', 'Guiné-Conacri'),
	('GQ', 'Guiné Equatorial'),
	('HT', 'Haiti'),
	('HM', 'Heard e Ilhas McDonald, Ilha'),
	('NL', 'Holanda (Países Baixos)'),
	('HN', 'Honduras'),
	('HK', 'Hong Kong'),
	('HU', 'Hungria'),
	('YE', 'Iémen'),
	('IN', 'Índia'),
	('ID', 'Indonésia'),
	('IQ', 'Iraque'),
	('IR', 'Irão'),
	('IE', 'Irlanda'),
	('IS', 'Islândia'),
	('IL', 'Israel'),
	('IT', 'Itália'),
	('JM', 'Jamaica'),
	('JP', 'Japão'),
	('JO', 'Jordânia'),
	('KW', 'Koweit'),
	('LA', 'Laos'),
	('LS', 'Lesoto'),
	('LV', 'Letónia'),
	('LB', 'Líbano'),
	('LR', 'Libéria'),
	('LY', 'Líbia'),
	('LI', 'Liechtenstein'),
	('LT', 'Lituânia'),
	('LU', 'Luxemburgo'),
	('MO', 'Macau'),
	('MK', 'Macedónia'),
	('MG', 'Madagáscar'),
	('MY', 'Malásia'),
	('MW', 'Malawi'),
	('MV', 'Maldivas'),
	('ML', 'Mali'),
	('MT', 'Malta'),
	('FK', 'Malvinas, Ilhas (Falkland)'),
	('MP', 'Marianas Setentrionais'),
	('MA', 'Marrocos'),
	('MH', 'Marshall, Ilhas'),
	('MQ', 'Martinica'),
	('MU', 'Maurícias'),
	('MR', 'Mauritânia'),
	('YT', 'Mayotte'),
	('UM', 'Menores Distantes dos Estados Unidos, Ilhas'),
	('MX', 'México'),
	('MM', 'Mianmar (antiga Birmânia)'),
	('FM', 'Micronésia, Estados Federados da'),
	('MD', 'Moldávia'),
	('MC', 'Mónaco'),
	('MN', 'Mongólia'),
	('MS', 'Montserrat'),
	('MZ', 'Moçambique'),
	('NA', 'Namíbia'),
	('NR', 'Nauru'),
	('NP', 'Nepal'),
	('NI', 'Nicarágua'),
	('NE', 'Níger'),
	('NG', 'Nigéria'),
	('NU', 'Niue'),
	('NF', 'Norfolk, Ilha'),
	('NO', 'Noruega'),
	('NC', 'Nova Caledónia'),
	('NZ', 'Nova Zelândia (Aotearoa)'),
	('OM', 'Oman'),
	('PW', 'Palau'),
	('PS', 'Palestina'),
	('PA', 'Panamá'),
	('PG', 'Papua-Nova Guiné'),
	('PK', 'Paquistão'),
	('PY', 'Paraguai'),
	('PE', 'Peru'),
	('PN', 'Pitcairn'),
	('PF', 'Polinésia Francesa'),
	('PL', 'Polónia'),
	('PR', 'Porto Rico'),
	('QA', 'Qatar'),
	('KE', 'Quénia'),
	('KG', 'Quirguistão'),
	('KI', 'Quiribati'),
	('GB', 'Reino Unido da Grã-Bretanha e Irlanda do Norte'),
	('RE', 'Reunião'),
	('RO', 'Roménia'),
	('RW', 'Ruanda'),
	('RU', 'Rússia'),
	('EH', 'Saara Ocidental'),
	('AS', 'Samoa Americana'),
	('WS', 'Samoa Ocidental'),
	('PM', 'Saint Pierre et Miquelon'),
	('SB', 'Salomão, Ilhas'),
	('KN', 'São Cristóvão e Névis (Saint Kitts e Nevis)'),
	('SM', 'São Marino'),
	('ST', 'São Tomé e Príncipe'),
	('VC', 'São Vicente e Granadinas'),
	('SH', 'Santa Helena'),
	('LC', 'Santa Lucia'),
	('SN', 'Senegal'),
	('SL', 'Serra Leoa'),
	('CS', 'Sérvia e Montenegro'),
	('SC', 'Seychelles'),
	('SG', 'Singapura'),
	('SY', 'Síria'),
	('SO', 'Somália'),
	('LK', 'Sri Lanka'),
	('SZ', 'Suazilândia'),
	('SD', 'Sudão'),
	('SE', 'Suécia'),
	('CH', 'Suíça'),
	('SR', 'Suriname'),
	('SJ', 'Svalbard e Jan Mayen'),
	('TH', 'Tailândia'),
	('TW', 'Taiwan'),
	('TJ', 'Tajiquistão'),
	('TZ', 'Tanzânia'),
	('TF', 'Terras Austrais e Antárticas Francesas (TAAF)'),
	('IO', 'Território Britânico do Oceano Índico'),
	('TL', 'Timor Leste (Timor Lorosae)'),
	('TG', 'Togo'),
	('TK', 'Tokelau'),
	('TO', 'Tonga'),
	('TT', 'Trindade e Tobago'),
	('TN', 'Tunísia'),
	('TC', 'Turcas e Caicos'),
	('TM', 'Turquemenistão'),
	('TR', 'Turquia'),
	('TV', 'Tuvalu'),
	('UA', 'Ucrânia'),
	('UG', 'Uganda'),
	('UY', 'Uruguai'),
	('UZ', 'Usbequistão'),
	('VU', 'Vanuatu'),
	('VA', 'Vaticano'),
	('VE', 'Venezuela'),
	('VN', 'Vietname'),
	('VI', 'Virgens Americanas, Ilhas'),
	('VG', 'Virgens Britânicas, Ilhas'),
	('WF', 'Wallis e Futuna'),
	('ZM', 'Zâmbia'),
	('ZW', 'Zimbabwé'),
	('OF', 'Outros países Africanos'),
	('ON', 'Outros países Americanos'),
	('OS', 'Outros países Asiáticos'),
	('OC', 'Outros países da Oceania'),
	('OE', 'Outros países Europeus'),
	('XR', 'Regiões polares'),
	('QU', 'Países e territórios ignorados')
)	

class CountryField(models.CharField):
    
	def __init__(self, *args, **kwargs):
		kwargs.setdefault('max_length', 2)
		kwargs.setdefault('choices', COUNTRIES)
		kwargs.setdefault('default', 'PT')
		super(CountryField, self).__init__(*args, **kwargs)


class PhoneField(models.CharField):
	default_validators = [validate_tels]
    
	def __init__(self, *args, **kwargs):
		kwargs.setdefault('max_length', 30)
		super(PhoneField, self).__init__(*args, **kwargs)


class NIBField(models.CharField):
	default_validators = [validate_nib]
    
	def __init__(self, *args, **kwargs):
		kwargs.setdefault('max_length', 21)
		super(NIBField, self).__init__(*args, **kwargs)		


class IBANField(models.CharField):
	default_validators = [validate_iban]
    
	def __init__(self, *args, **kwargs):
		kwargs.setdefault('max_length', 34)
		super(IBANField, self).__init__(*args, **kwargs)		


class NIFField(models.CharField):
	default_validators = [validate_nif]
    
	def __init__(self, *args, **kwargs):
		kwargs.setdefault('max_length', 15)
		super(NIFField, self).__init__(*args, **kwargs)			

class NIFFormField(fields.CharField):
	default_validators = [validate_nif]
	def __init__(self, *args, **kwargs):
		kwargs.setdefault('max_length', 15)
		super(NIFFormField, self).__init__(*args, **kwargs)	


class NISSField(models.CharField):
	default_validators = [validate_niss]
    
	def __init__(self, *args, **kwargs):
		kwargs.setdefault('max_length', 11)
		super(NISSField, self).__init__(*args, **kwargs)	


class CurrencyField(models.DecimalField):
    __metaclass__ = models.SubfieldBase

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('decimal_places', 2)
        kwargs.setdefault('max_digits', 10)
        super(CurrencyField, self). __init__(*args, **kwargs)

    def to_python(self, value):
        try:
            return super(CurrencyField, self).to_python(value).quantize(Decimal("0.01"))
        except AttributeError:
            return None		


from south.modelsinspector import add_introspection_rules

add_introspection_rules([], ["^core\.fields\.CountryField", "^core\.fields\.PhoneField", "^core\.fields\.CurrencyField",
	                         "^core\.fields\.NIFField", "^core\.fields\.NIBField", "^core\.fields\.IBANField",
	                         "^core\.fields\.NISSField"])


