from docassemble.base.core import DAObject, DAList, DADict, DAOrderedDict
from docassemble.base.util import Value, PeriodicValue, FinancialList, PeriodicFinancialList, DAEmpty
from decimal import Decimal
import datetime
import docassemble.base.functions
from collections import OrderedDict
import json


def flatten(listname,index=1):
	"""Return just the nth item in an 2D list. Intended to use for multiple choice option lists in Docassemble.
		e.g., flatten(asset_type_list()) will return ['Savings','Certificate of Deposit'...] """
	return [item[index] for item in listname]

def income_period_list():
	return [
		[12,"Monthly"],
		[1,"Yearly"],
		[52,"Weekly"],
		[24,"Twice per month"],
		[26,"Once every two weeks"],
		[4,"Once every 3 months"]
	]

def income_period(index):
	try:
		for row in income_period_list():
			if int(index) == int(row[0]):
				return row[1].lower()
		return docassemble.base.functions.nice_number(int(index), capitalize=True) + " " + docassemble.base.functions.word("times per year")
	except:
		return ''
	return ''

docassemble.base.functions.update_language_function('*', 'period_list', income_period_list)

def recent_years(years=15, order='descending',future=1):
	"""Returns a list of the most recent years, continuing into the future. Defaults to most recent 15 years+1. Useful to populate
		a combobox of years where the most recent ones are most likely. E.g. automobile years or birthdate.
		Keyword paramaters: years, order (descending or ascending), future (defaults to 1)"""
	now = datetime.datetime.now()
	if order=='ascending':
		return list(range(now.year-years,now.year+future,1))
	else:
		return list(range(now.year+future,now.year-years,-1))

def asset_type_list() :
	"""Returns a list of assset types for a multiple choice dropdown"""
	type_list = DAOrderedDict()
	type_list.auto_gather = False
	type_list.gathered = True
	type_list.elements.update([
		('savings', 'Savings Account'),
		('stocks', 'Stocks '),
		('trust', 'Trust Fund'),
		('checking', 'Checking Account'),
		('vehicle', 'Cars'),
		('real estate', 'Real Estate'),
		('other', 'Other Asset')
	])
	return type_list

def income_type_list() :
	"""Returns a dict of income types for a multiple choice dropdown"""
	type_list = DAOrderedDict()
	type_list['wages'] = 'A job or self-employment'

	type_list.elements.update(non_wage_income_list())
	type_list.auto_gather = False
	type_list.gathered = True

	return type_list

def non_wage_income_list():
	"""Returns a dict of income types, excluding wages"""
	type_list = DAOrderedDict()
	type_list.auto_gather = False
	type_list.gathered = True
	type_list.elements.update([
		('SSR', 'Social Security Retirement Benefits'),
		('SSDI', 'Social Security Disability Benefits'),
		('SSI', 'Supplemental Security Income (SSI)'),
		('pension', 'Pension'),
		('TAFDC', 'TAFDC'),
		('public assistance', 'Other public assistance'),
		('SNAP', 'Food Stamps (SNAP)'),
		('rent', 'Income from real estate (rent, etc)'),
		('room and board', 'Room and/or Board Payments'),
		('child support', 'Child Support'),
		('alimony', 'Alimony'),
		('other support', 'Other Support'),
		('other', 'Other')
	])
	return type_list

def expense_type_list() :
	"""Returns a dict of expense types for a multiple choice dropdown"""
	type_list = DAOrderedDict()
	type_list.auto_gather = False
	type_list.gathered = True
	type_list.elements.update([
		('Rent', 'Rent'),
		('Mortgage', 'Mortgage'),
		('Food & Non-Alcoholic Drinks', 'Food & Non-Alcoholic Drinks'),
		('Alcoholic drink, tobacco &carcotics', 'Alcoholic drink, tobacco &carcotics'),
		('Utilities', 'Utilities'),
		('Fuel & Power', 'Fuel & Power'),
		('Clothing & Footwear', 'Clothing & Footwear'),
		('Credit Card Payments', 'Credit Card Payments'),
		('Hotels & Restaurants', 'Hotels & Restaurants'),
		('Transport', 'Transport'),
		('Communication','Communication'),
		('Education','Education'),
		('Health', 'Health'),
		('Auto', 'Car operation and maintenance'),
		('Loan payments', 'Loan, credit, or lay-away payments'),
		('Support', 'Support to someone not in household'),
		('Other', 'Other')
	])
	return type_list


class Income(PeriodicValue):
	"""Represents a job which may have an hourly rate or a salary.
		Hourly rate jobs must include hours and period. 
		Period is some demoninator of a year for compatibility with
		PeriodicFinancialList class. E.g, to express hours/week, use 52 """

	def amount(self, period_to_use=1):
		"""Returns the amount earned over the specified period """
		# Can't remember why I added the below so let's see what commenting
		# it out breaks...
		#if not hasattr(self, 'value') or self.value == '':
		#	value = 0
		#else:
		#	value = self.value
		#if not hasattr(self, 'period') or self.period == '':
		#	period = 1
		#else:
		#	period = self.period
		if hasattr(self, 'is_hourly') and self.is_hourly:
			return Decimal(self.hourly_rate * self.hours_per_period * self.period) / Decimal(period_to_use)
		return (Decimal(self.value) * Decimal(self.period)) / Decimal(period_to_use)

class Job(Income):
	"""Represents a job that may be hourly or pay-period based. If non-hourly, may specify gross and net income amounts"""
	def net_amount(self, period_to_use=1):
		"""Returns the net amount (e.g., minus deductions). Only applies if value is non-hourly."""
		return (Decimal(self.net) * Decimal(self.period)) / Decimal(period_to_use)
 
	def gross_amount(self, period_to_use=1):
		"""Gross amount is identical to value"""
		return self.amount(period_to_use = period_to_use)

	def name_address_phone(self):
		"""Returns concatenation of name, address and phone number of employer"""
		return self.employer + ': ' + self.employer_address + ', ' + self.employer_phone
	
	def normalized_hours(self, period_to_use):
		"""Returns the number of hours worked in a given period"""
		return (float(self.hours_per_period) * int(self.period)) / int(period_to_use)

class Asset(Income):
	"""
	Like income but with an optional value.
	"""
	def amount(self, period_to_use=1):
		if not hasattr(self, 'value'):
			return 0
		else:
			return super(Asset, self).amount(period_to_use=period_to_use)
		
class SimpleValue(DAObject):
	"""Like a Value object, but no fiddling around with .exists attribute because it's designed to store in a list, not a dictionary"""
	def amount(self):
		"""If desired, to use as a ledger, values can be signed. setting transaction_type = 'expense' makes the value negative. Use min=0 in that case."""
		if hasattr(self, 'transaction_type'):
			return (self.value * -1) if (self.transaction_type == 'expense') else self.value
		else:
			return self.value

	def __str__(self):
		return str(self.amount())
		
class Debt(SimpleValue):
	def init(self, *pargs, **kwargs):
		super(Debt, self).init(*pargs, **kwargs)
		
class ConsumerDebt(Debt):
	def init(self, *pargs, **kwargs):
		super(ConsumerDebt, self).init(*pargs, **kwargs)

		
class LiabilityDebt(Debt):
	def init(self, *pargs, **kwargs):
		super(LiabilityDebt, self).init(*pargs, **kwargs)

		
class LoansDebt(Debt):
	def init(self, *pargs, **kwargs):
		super(LoansDebt, self).init(*pargs, **kwargs)

class PenaltiesDebt(Debt):
	def init(self, *pargs, **kwargs):
		super(PenaltiesDebt, self).init(*pargs, **kwargs)

class TaxDebt(Debt):
	def init(self, *pargs, **kwargs):
		super(TaxDebt, self).init(*pargs, **kwargs)

class RevolvingCreditDebt(LoansDebt):
	def init(self, *pargs, **kwargs):
		super(RevolvingCreditDebt, self).init(*pargs, **kwargs)

class CreditCardDebt(RevolvingCreditDebt):
	def init(self, *pargs, **kwargs):
		super(CreditCardDebt, self).init(*pargs, **kwargs)

class ChargeCard(RevolvingCreditDebt):
	def init(self, *pargs, **kwargs):
		super(ChargeCard, self).init(*pargs, **kwargs)

class BankOverdraft(RevolvingCreditDebt):
	def init(self, *pargs, **kwargs):
		super(BankOverdraft, self).init(*pargs, **kwargs)

class BudgetAccount(RevolvingCreditDebt):
	def init(self, *pargs, **kwargs):
		super(BudgetAccount, self).init(*pargs, **kwargs)

class MortgageDebt(LoansDebt):
	def init(self, *pargs, **kwargs):
		super(MortgageDebt, self).init(*pargs, **kwargs)

class PersonalLoan(LoansDebt):
	def init(self, *pargs, **kwargs):
		super(PersonalLoan, self).init(*pargs, **kwargs)

class StudentLoans(LoansDebt):
	def init(self, *pargs, **kwargs):
		super(StudentLoans, self).init(*pargs, **kwargs)

class InformalLoan(LoansDebt):
	def init(self, *pargs, **kwargs):
		super(InformalLoan, self).init(*pargs, **kwargs)

class HirePurchase(LoansDebt):
	def init(self, *pargs, **kwargs):
		super(HirePurchase, self).init(*pargs, **kwargs)

class PaydayLoan(LoansDebt):
	def init(self, *pargs, **kwargs):
		super(PaydayLoan, self).init(*pargs, **kwargs)

class BillOfSale(LoansDebt):
	def init(self, *pargs, **kwargs):
		super(BillOfSale, self).init(*pargs, **kwargs)

class Pawnbroker(LoansDebt):
	def init(self, *pargs, **kwargs):
		super(Pawnbroker, self).init(*pargs, **kwargs)

class TradingCheque(LoansDebt):
	def init(self, *pargs, **kwargs):
		super(TradingCheque, self).init(*pargs, **kwargs)

class CreditSaleAgreement(LoansDebt):
	def init(self, *pargs, **kwargs):
		super(CreditSaleAgreement, self).init(*pargs, **kwargs)

class InterestFreeCredit(LoansDebt):
	def init(self, *pargs, **kwargs):
		super(InterestFreeCredit, self).init(*pargs, **kwargs)

class CatalogueSpending(LoansDebt):
	def init(self, *pargs, **kwargs):
		super(CatalogueSpending, self).init(*pargs, **kwargs)

class RentDebt(ConsumerDebt):
	def init(self, *pargs, **kwargs):
		super(RentDebt, self).init(*pargs, **kwargs)

class EnergyBillArrears(ConsumerDebt):
	def init(self, *pargs, **kwargs):
		super(EnergyBillArrears, self).init(*pargs, **kwargs)

class WaterArrears(ConsumerDebt):
	def init(self, *pargs, **kwargs):
		super(WaterArrears, self).init(*pargs, **kwargs)

class NonRegularBill(ConsumerDebt):
	def init(self, *pargs, **kwargs):
		super(NonRegularBill, self).init(*pargs, **kwargs)

class PrivateParkingCharge(ConsumerDebt):
	def init(self, *pargs, **kwargs):
		super(PrivateParkingCharge, self).init(*pargs, **kwargs)

class TVLicenseDebt(TaxDebt):
	def init(self, *pargs, **kwargs):
		super(TVLicenseDebt, self).init(*pargs, **kwargs)

class NationalTax(TaxDebt):
	def init(self, *pargs, **kwargs):
		super(NationalTax, self).init(*pargs, **kwargs)

class IncomeTax(NationalTax):
	def init(self, *pargs, **kwargs):
		super(IncomeTax, self).init(*pargs, **kwargs)

class NationalInsurance(NationalTax):
	def init(self, *pargs, **kwargs):
		super(NationalInsurance, self).init(*pargs, **kwargs)

class ValueAddedTax(NationalTax):
	def init(self, *pargs, **kwargs):
		super(ValueAddedTax, self).init(*pargs, **kwargs)

class NonDomesticRates(TaxDebt):
	def init(self, *pargs, **kwargs):
		super(NonDomesticRates, self).init(*pargs, **kwargs)

class CouncilTax(TaxDebt):
	def init(self, *pargs, **kwargs):
		super(CouncilTax, self).init(*pargs, **kwargs)

class OverpaymentOfBenefits(TaxDebt):
	def init(self, *pargs, **kwargs):
		super(OverpaymentOfBenefits, self).init(*pargs, **kwargs)

class SocialFundLoan(OverpaymentOfBenefits):
	def init(self, *pargs, **kwargs):
		super(SocialFundLoan, self).init(*pargs, **kwargs)

class UniversalCreditAdvance(OverpaymentOfBenefits):
	def init(self, *pargs, **kwargs):
		super(UniversalCreditAdvance, self).init(*pargs, **kwargs)

class TaxCreditOverpayment(OverpaymentOfBenefits):
	def init(self, *pargs, **kwargs):
		super(TaxCreditOverpayment, self).init(*pargs, **kwargs)

class Fine(PenaltiesDebt):
	def init(self, *pargs, **kwargs):
		super(Fine, self).init(*pargs, **kwargs)

class PenaltyChargeDebt(PenaltiesDebt):
	def init(self, *pargs, **kwargs):
		super(PenaltyChargeDebt, self).init(*pargs, **kwargs)

class TrafficPenaltiesDebt(PenaltiesDebt):
	def init(self, *pargs, **kwargs):
		super(TrafficPenaltiesDebt, self).init(*pargs, **kwargs)

class ChildSupport(LiabilityDebt):
	def init(self, *pargs, **kwargs):
		super(ChildSupport, self).init(*pargs, **kwargs)

class CivilDamages(LiabilityDebt):
	def init(self, *pargs, **kwargs):
		super(CivilDamages, self).init(*pargs, **kwargs)

class Maintenance(LiabilityDebt):
	def init(self, *pargs, **kwargs):
		super(Maintenance, self).init(*pargs, **kwargs)

class ShopliftingRecovery(LiabilityDebt):
	def init(self, *pargs, **kwargs):
		super(ShopliftingRecovery, self).init(*pargs, **kwargs)
		
class Vehicle(SimpleValue):
	"""Vehicles have a method year_make_model() """
	def year_make_model(self):
		return self.year + ' / ' + self.make + ' / ' + self.model

class ValueList(DAList):
	"""Represents a filterable DAList of SimpleValues"""
	def init(self, *pargs, **kwargs):
		super(ValueList, self).init(*pargs, **kwargs)
		self.object_type = SimpleValue

	def types(self):
		"""Returns a set of the unique types of values stored in the list. Will fail if any items in the list leave the type field unspecified"""
		types = set()
		for item in self.elements:
			if hasattr(item,'type'):
				types.add(item.type)
		return types
		
	def total(self, type=None):
		"""Returns the total value in the list, gathering the list items if necessary.
		You can specify type, which may be a list, to coalesce multiple entries of the same type."""
		self._trigger_gather()
		result = 0
		if type is None:
			for item in self.elements:
				#if self.elements[item].exists:
				result += Decimal(item.amount())
		elif isinstance(type, list):
			for item in self.elements:
				if item.type in type:
					result += Decimal(item.amount())
		else:
			for item in self.elements:
				if item.type == type:
					result += Decimal(item.amount())
		return result

class ValueListNoObject(DAList):
	"""Represents a filterable DAList of SimpleValues"""
	def init(self, *pargs, **kwargs):
		super(ValueListNoObject, self).init(*pargs, **kwargs)

	def types(self):
		"""Returns a set of the unique types of values stored in the list. Will fail if any items in the list leave the type field unspecified"""
		types = set()
		for item in self.elements:
			if hasattr(item,'type'):
				types.add(item.type)
		return types
		
	def total(self, type=None):
		"""Returns the total value in the list, gathering the list items if necessary.
		You can specify type, which may be a list, to coalesce multiple entries of the same type."""
		self._trigger_gather()
		result = 0
		if type is None:
			for item in self.elements:
				#if self.elements[item].exists:
				result += Decimal(item.amount())
		elif isinstance(type, list):
			for item in self.elements:
				if item.type in type:
					result += Decimal(item.amount())
		else:
			for item in self.elements:
				if item.type == type:
					result += Decimal(item.amount())
		return result

def DebtList(DAList):
	def init(self, *pargs, **kwargs):
		super(Debt, self).init(*pargs, **kwargs)

	def types(self):
		"""Returns a set of the unique types of values stored in the list. Will fail if any items in the list leave the type field unspecified"""
		types = set()
		for item in self.elements:
			if hasattr(item,'type'):
				types.add(item.type)
		return types
		
	def total(self, type=None):
		"""Returns the total value in the list, gathering the list items if necessary.
		You can specify type, which may be a list, to coalesce multiple entries of the same type."""
		self._trigger_gather()
		result = 0
		if type is None:
			for item in self.elements:
				#if self.elements[item].exists:
				result += Decimal(item.amount())
		elif isinstance(type, list):
			for item in self.elements:
				if item.type in type:
					result += Decimal(item.amount())
		else:
			for item in self.elements:
				if item.type == type:
					result += Decimal(item.amount())
		return result

		
class Ledger(ValueList):
	"""Represents an account ledger. Adds calculate method which adds a running total to the ledger."""
	def init(self, *pargs, **kwargs):
		super(Ledger, self).init(*pargs, **kwargs)

	def calculate(self):
		""" Sort the ledger by date, then add a running total to each ledger entry"""
		self.elements.sort(key=lambda y: y.date)
		running_total = 0
		for entry in self.elements:
			running_total += entry.amount()
			entry.running_total = running_total

class VehicleList(ValueList):
	"""List of vehicles, extends ValueList. Vehicles have a method year_make_model() """
	def init(self, *pargs, **kwargs):
		super(VehicleList, self).init(*pargs, **kwargs)
		self.object_type = Vehicle

class IncomeList(DAList):
	"""Represents a filterable DAList of income items, each of which has an associated period or hourly wages."""
	
	def init(self, *pargs, **kwargs):
		self.elements = list()
		if not hasattr(self, 'object_type'):
			self.object_type = Income
		return super(IncomeList, self).init(*pargs, **kwargs)
	def types(self):
		"""Returns a set of the unique types of values stored in the list."""
		types = set()
		for item in self.elements:
			if hasattr(item,'type'):
				types.add(item.type)
		return types

	def owners(self, type=None):
		"""Returns a set of the unique owners for the specified type of value stored in the list. If type is None, returns all 
		unique owners in the IncomeList"""
		owners=set()
		if type is None:
			for item in self.elements:
				if hasattr(item, 'owner'):
					owners.add(item.owner)
		elif isinstance(type, list):
			for item in self.elements:
				if hasattr(item,'owner') and hasattr(item,'type') and item.type in type:
					owners.add(item.owner)
		else:
			for item in self.elements:
				if hasattr(item,'owner') and item.type == type:
					owners.add(item.owner)
		return owners

	def matches(self, type):
		"""Returns an IncomeList consisting only of elements matching the specified Income type, assisting in filling PDFs with predefined spaces. Type may be a list"""
		if isinstance(type, list):
			return IncomeList(elements = [item for item in self.elements if item.type in type])
		else:
			return IncomeList(elements = [item for item in self.elements if item.type == type])

	def total(self, period_to_use=1, type=None,owner=None):
		"""Returns the total periodic value in the list, gathering the list items if necessary.
		You can specify type, which may be a list, to coalesce multiple entries of the same type.
		Similarly, you can specify owner."""
		self._trigger_gather()
		result = 0
		if period_to_use == 0:
			return(result)
		if type is None:
			for item in self.elements:
				#if self.elements[item].exists:
				result += Decimal(item.amount(period_to_use=period_to_use))
		elif isinstance(type, list):
			for item in self.elements:
				if item.type in type:
					if owner is None: # if we don't care who the owner is
						result += Decimal(item.amount(period_to_use=period_to_use))
					else:
						if not (isinstance(owner, DAEmpty)) and item.owner == owner:
							result += Decimal(item.amount(period_to_use=period_to_use))
		else:
			for item in self.elements:
				if item.type == type:
					if owner is None:
						result += Decimal(item.amount(period_to_use=period_to_use))
					else:
						if not (isinstance(owner, DAEmpty)) and item.owner == owner:
							result += Decimal(item.amount(period_to_use=period_to_use))
		return result
	
	def market_value_total(self, type=None):
		"""Returns the total market value of values in the list."""
		result = 0
		for item in self.elements:
			if type is None:
				result += Decimal(item.market_value)
			elif isinstance(type, list): 
				if item.type in type:
					result += Decimal(item.market_value)
			else:
				if item.type == type:
					result += Decimal(item.market_value)
		return result


	def balance_total(self, type=None):
		self._trigger_gather()
		result = 0
		for item in self.elements:
			if type is None:
				result += Decimal(item.balance)
			elif isinstance(type, list): 
				if item.type in type:
					result += Decimal(item.balance)
			else:
				if item.type == type:
					result += Decimal(item.balance)
		return result
	
	def to_json(self):
		"""Creates income list suitable for Legal Server API"""
		return json.dumps([{"type": income.type, "frequency": income.period, "amount": income.value} for income in self.elements])

class JobList(IncomeList):
	"""Represents a list of jobs. Adds the net_total and gross_total methods to the IncomeList class"""
	def init(self, *pargs, **kwargs):
		# self.elements = list()
		super(JobList, self).init(*pargs, **kwargs)
		self.object_type = Job
	
	def gross_total(self, period_to_use=1, type=None):
		self._trigger_gather()
		result = 0
		if period_to_use == 0:
			return(result)
		if type is None:
			for item in self.elements:
				#if self.elements[item].exists:
				result += Decimal(item.gross_amount(period_to_use=period_to_use))
		elif isinstance(type, list):
			for item in self.elements:
				if item.type in type:
					result += Decimal(item.gross_amount(period_to_use=period_to_use))
		else:
			for item in self.elements:
				if item.type == type:
					result += Decimal(item.gross_amount(period_to_use=period_to_use))
		return result
	def net_total(self, period_to_use=1, type=None):
		self._trigger_gather()
		result = 0
		if period_to_use == 0:
			return(result)
		if type is None:
			for item in self.elements:
				#if self.elements[item].exists:
				result += Decimal(item.net_amount(period_to_use=period_to_use))
		elif isinstance(type, list):
			for item in self.elements:
				if item.type in type:
					result += Decimal(item.net_amount(period_to_use=period_to_use))
		else:
			for item in self.elements:
				if item.type == type:
					result += Decimal(item.net_amount(period_to_use=period_to_use))
		return result

class AssetList(IncomeList):
	def init(self, *pargs, **kwargs):
		super(AssetList, self).init(*pargs, **kwargs)
		self.object_type = Asset
