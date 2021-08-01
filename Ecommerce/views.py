#pip install --upgrade stripe

import random
import string
import stripe
from django.conf import settings
from django.shortcuts import render,get_object_or_404
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.views.generic import ListView,DetailView,View
from .models import Item,OrderItem,Order,Address
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import CheckoutForm,CouponForm,RefundForm
from .models import Item, OrderItem, Order,Payment,Coupon,Refund
stripe.api_key = settings.STRIPE_SECRET_KEY
def create_ref_code():
	 return ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))


def products(request):
    context = {
        'items': Item.objects.all()
    }
    return render(request, "products.html", context)

def is_valid_form(values):
	valid=True
	for field in values:
		if field =='':
			valid=false
	return valid


class HomeView(ListView):
	model=Item
	paginate_by=10
	template_name="home.html"
class CheckoutView(View):
	def get(self, *args, **kwargs):
		try:
			order=Order.objects.get(user=self.request.user,ordered=False)
			form=CheckoutForm()
			context={
				'form':form,
				'order':order,
				'couponform':CouponForm(),
				'DISPLAY_COUPON_FORM': True
				}
			print("yo1")
			shipping_address_qs=Address.objects.filter(user=self.request.user,address_type='S',default=True)
			if shipping_address_qs.exists():
				context.update({'default_shipping_address':shipping_address_qs[0]})
			billing_address_qs=Address.objects.filter(user=self.request.user,address_type='B',default=True)
			if billing_address_qs.exists():
				context.update({'default_billing_address':billing_address_qs[0]})
			return render(self.request, 'checkout.html',context)
		except ObjectDoesNotExist:
			messages.info(self.request.user, "You do not have an active order")
			return redirect("Ecommerce:checkout")
		
		
	def post(self, *args, **kwargs):
		form=CheckoutForm(self.request.POST or None)
		try:
			order = Order.objects.get(user=self.request.user, ordered=False)
			if form.is_valid():
				print("inside form is valid")
				use_default_shipping=form.cleaned_data.get("use_default_shipping")
				if use_default_shipping:
					print("using default")
					address_qs=Address.objects.filter(
								user=self.request.user,
								address_type='S',
								default=True)
					if address_qs.exists():
						shipping_address=address_qs[0]
						order.shipping_address = shipping_address
						order.save()
					else:
						messages.info(self.request,"no default available")
						return redirect( "Ecommerce:checkout")
				else:
					print("user is enytering it")
					
					shipping_address1=form.cleaned_data.get('shipping_address')
					shipping_address2=form.cleaned_data.get('shipping_address2')
					shipping_country=form.cleaned_data.get('shipping_country')
					shipping_zip=form.cleaned_data.get('shipping_zip')
					
					if is_valid_form([shipping_address1, shipping_country, shipping_zip]):
					
						shipping_address=Address(user=self.request.user,
						street_address=shipping_address1,
						apartment_address=shipping_address2,
						country=shipping_country,
						zip=shipping_zip,
						address_type='S')
						shipping_address.save()
						order.shipping_address=shipping_address
						order.save()
						set_default_shipping = form.cleaned_data.get('set_default_shipping')
						if set_default_shipping:
							shipping_address.default = True
							shipping_address.save()
					else:
						messages.warning(self.request,"enter all fields please")
						return redirect( "Ecommerce:checkout")

				use_default_billing=form.cleaned_data.get('use_default_billing')
				same_billing_address=form.cleaned_data.get('same_billing_address')
				if same_billing_address:
					billing_address=shipping_address
					billing_address.pk=None
					billing_address.save()
					billing_address.address_type='B'
					billing_address.save()
					order.billing_address=billing_address
					order.save()
				elif use_default_billing:
					print("using default")
					address_qs=Address.objects.filter(
								user=self.request.user,
								address_type='B',
								default=True)
					if address_qs.exists():
						billing_address=address_qs[0]
						order.billing_address = billing_address
						order.save()
					else:
						messages.info(self.request,"no default available")
						return redirect( "Ecommerce:checkout")
				else:
					print("user is enytering it")
					
					billing_address1=form.cleaned_data.get('billing_address')
					billing_address2=form.cleaned_data.get('billing_address2')
					billing_country=form.cleaned_data.get('billing_country')
					billing_zip=form.cleaned_data.get('billing_zip')
			
					
					
					if is_valid_form([billing_address1, billing_country,billing_zip]):
					
						billing_address=Address(user=self.request.user,
street_address=billing_address1,
apartment_address=billing_address2,
country=billing_country,
zip=billing_zip,
address_type='B')
						billing_address.save()
						order.billing_address=billing_address
						order.save()
						set_default_billing = form.cleaned_data.get('set_default_billing')
						if set_default_billing:
							billing_address.default = True
							billing_address.save()
						print(form.cleaned_data)
						print("is valid")
					else:
						messages.warning(self.request,"enter all fields please")
						return redirect( "Ecommerce:checkout")
				payment_option =form.cleaned_data.get("payment_option")
				if payment_option == 'S':
					return redirect('Ecommerce:payment', payment_option='stripe')
				elif payment_option == 'P':
					return redirect('Ecommerce:payment', payment_option='paypal')
				else:
					messages.warning(
					self.request, "Invalid payment option selected")
					return redirect('Ecommerce:checkout')
					



			messages.warning(self.request,"failed checkout")
			return redirect( "Ecommerce:checkout")
		except ObjectDoesNotExist:
			messages.warning(self.request, "You do not have an active order")
			return redirect("Ecommerce:order-summary")





class PaymentView(View):
	print("yes")
	def get(self, *args,**kwargs):
		print("yolo")
		order = Order.objects.get(user=self.request.user, ordered=False)
		if order.billing_address:
			context = {
				'order': order,
				'DISPLAY_COUPON_FORM': False,
				'STRIPE_PUBLIC_KEY' : settings.STRIPE_PUBLIC_KEY}
			userprofile = self.request.user.userprofile
			if userprofile.one_click_purchasing:
				cards = stripe.Customer.list_sources(
					userprofile.stripe_customer_id,
					limit=3,
					object='card'
					)
				card_list = cards['data']
				if len(card_list) > 0:
                    
					context.update({
						'card': card_list[0]})
			return render(self.request,"payment.html",context)
		else:
			messages.warning(self.request,"no billing address mentioned") 
			return redirect( "Ecommerce:checkout")
	def post(self, *args,**kwargs):
		print("here atlleasy")
		order=Order.objects.get(user=self.request.user,ordered=False)
		form = PaymentForm(self.request.POST)
		userprofile = UserProfile.objects.get(user=self.request.user)
		if form.is_valid():
			token=self.request.POST.get('stripeToken')
			save = form.cleaned_data.get('save')
			use_default = form.cleaned_data.get('use_default')
			if save:
				if userprofile.stripe_customer_id != '' and userprofile.stripe_customer_id is not None:
					customer = stripe.Customer.retrieve(
						userprofile.stripe_customer_id)
					customer.sources.create(source=token)

				else:
					customer = stripe.Customer.create(
					email=self.request.user.email,)
					customer.sources.create(source=token)
					userprofile.stripe_customer_id = customer['id']
					userprofile.one_click_purchasing = True
					userprofile.save()

			amount = int(order.get_total() * 100)
			#amount=int(order.get_total()*100)
			try:
				if use_default or save:
					charge=stripe.Charge.create(
						amount=amount,
						currency="usd",
						customer=userprofile.stripe_customer_id)
				else:
					charge = stripe.Charge.create(
						amount=amount,  # cents
						currency="usd",
						source=token)
			
				payment=Payment()
				payment.stripe_charge_id=charge['id']
				payment.user=self.request.user
				payment.amount= order.get_total()
				payment.save()
			
				order_items=order.items.all()
				order_items.update(ordered=True)
				for item in order_items:
					item.save()
				order.ordered=True
				order.payment=payment
			
				order.save()
				messages.success(self.request, "Your order was successful!")
				print("yay")
				return redirect("/")
  			# Use Stripe's library to make requests...
			
			except stripe.error.CardError as e:
				print('e')
				body = e.json_body
				err = body.get('error', {})
				messages.warning(self.request, f"{err.get('message')}")
				return redirect("/")
  			# Since it's a decline, stripe.error.CardError will be caught

			except stripe.error.RateLimitError as e:
				print('e')
  				# Too many requests made to the API too quickly
				messages.warning(self.request, "Rate limit error")
				return redirect("/")
			except stripe.error.InvalidRequestError as e:
				print('e')
  				# Invalid parameters were supplied to Stripe's API
				messages.warning(self.request, "Invalid parameters")
				return redirect("/")
			except stripe.error.AuthenticationError as e:
				print('e')
  				# Authentication with Stripe's API failed
  				# (maybe you changed API keys recently)
				messages.warning(self.request, "Not authenticated")
				return redirect("/")
			except stripe.error.APIConnectionError as e:
				print('e')
				# Network communication with Stripe failed
				messages.warning(self.request, "Network error")
				return redirect("/")
			except stripe.error.StripeError as e:
				print('e')
				# Display a very generic error to the user, and maybe send
				# yourself an email
				messages.warning(self.request, "Something went wrong. You were not charged. Please try again.")
				return redirect("/")
			except Exception as e:
				print('e')
  				# Something else happened, completely unrelated to Stripe
				messages.warning(self.request, "A serious error occurred. We have been notifed.")
				return redirect("/")
		messages.warning(self.request, "Invalid data received")
		return redirect("/payment/stripe/")

		
		
		
		

class OrderSummaryView(LoginRequiredMixin, View):
	def get(self, *args, **kwargs):
		try:
			order = Order.objects.get(user=self.request.user, ordered=False)
			context = {
				'object': order
			}
			return render(self.request, 'order_summary.html', context)
		except ObjectDoesNotExist:
			messages.warning(self.request, "You do not have an active order")
			return redirect("/")

class ItemDetailView(DetailView):
	model=Item
	template_name="product.html"

@login_required
def add_to_cart(request,slug):
	item=get_object_or_404(Item,slug=slug)
	order_item,created=OrderItem.objects.get_or_create(
	item=item,
	user=request.user,
	ordered=False

	)
	order_qs=Order.objects.filter(user=request.user,ordered=False)#ordered=False makes sure it is adding to orders that arent completed
#checking if the product is already added
	if order_qs.exists():
		order=order_qs[0]
		if order.items.filter(item__slug=item.slug).exists():
			order_item.quantity += 1
			order_item.save()
			messages.info(request, "This item was updated in your cart")
			return redirect ("Ecommerce:order-summary")
		else:
			messages.info(request, "This item was added in your cart")
			order.items.add(order_item)
			return redirect ("Ecommerce:Products",slug=slug)
	else:
		ordered_date=timezone.now()
		order=Order.objects.create(user=request.user,ordered_date=ordered_date)
		order.items.add(order_item)
		messages.info(request, "This item was added in your cart")
	return redirect ("Ecommerce:Products",slug=slug)

@login_required
def remove_from_cart(request,slug):
	item=get_object_or_404(Item,slug=slug)
	order_qs=Order.objects.filter(user=request.user,
	ordered=False)
#ordered=False makes sure it is adding to orders that arent completed
#checking if the product is already added
	if order_qs.exists():
		order=order_qs[0]
		if order.items.filter(item__slug=item.slug).exists():
			order_item=OrderItem.objects.filter(
				item=item,
				user=request.user,
				ordered=False
			)[0]
			order.items.remove(order_item)
			order_item.delete()
			messages.info(request, "This item was removed from your cart")
			return redirect("Ecommerce:order-summary")
			
		else:
			messages.info(request, "This item was not in your cart")
			return redirect("Ecommerce:Products",slug=slug)
	else:	
		messages.info(request, "You do not have an active order")
		#add amesaage that they dont have an order
		return redirect("Ecommerce:Products",slug=slug)
	return redirect("Ecommerce:Products",slug=slug)

@login_required
def remove_single_item_from_cart(request,slug):
	item=get_object_or_404(Item,slug=slug)
	order_qs=Order.objects.filter(user=request.user,
	ordered=False)
#ordered=False makes sure it is adding to orders that arent completed
#checking if the product is already added
	if order_qs.exists():
		order=order_qs[0]
		if order.items.filter(item__slug=item.slug).exists():
			order_item=OrderItem.objects.filter(
				item=item,
				user=request.user,
				ordered=False
			)[0]
			
			order_item.quantity -= 1
			order_item.save()
			messages.info(request, "This item was updated in your cart")
			return redirect("Ecommerce:order-summary")
			
			
		else:
			messages.info(request, "This item was not in your cart")
			return redirect("Ecommerce:Products",slug=slug)
	else:	
		messages.info(request, "You do not have an active order")
		#add amesaage that they dont have an order
		return redirect("Ecommerce:Products",slug=slug)
	return redirect("Ecommerce:Products",slug=slug)

def get_coupon(request,code):
	try:
		coupon=Coupon.objects.get(code=code)
		return coupon
	except ObjectDoesNotExist:
		messages.info(request, "this coupon dosent exist")
		return redirect("Ecommerce:checkout")
class AddCoupon(View):
	def post(self, *args,**kwargs):
		form=CouponForm(self.request.POST or None)
		if form.is_valid():
			try:
				code=form.cleaned_data.get('code')
				order=Order.objects.get(user=self.request.user,ordered=False)
				order.coupon=get_coupon(self.request,code)
				order.save()
				messages.info(self.request, "succesfully added coupon")
				return redirect("Ecommerce:checkout")
			except ObjectDoesNotExist:
				messages.info(self.request, "You do not have an active order")
				return redirect("Ecommerce:checkout")


class RequestRefundView(View):
	def get(self, *args,**kwargs):
		form=RefundForm()
		context={'form':form}

		return render(self.request,"request_refund.html",context)
	def post(self, *args,**kwargs):
		form=RefundForm(self.request.POST)
		if form.is_valid():
			ref_code=form.cleaned_data.get('ref_code')
			message=form.cleaned_data.get('message')
			email=form.cleaned_data.get('email')
			try:
				order=Order.objects.get(ref_code=ref_code)
				order.refund_requested=True
				order.save()
				refund=Refund()
				refund.order=order
				refund.reason=message
				refund.email=email
				refund.save()
				messages.info(self.request, "your request is recieved")
				print("ypooooo")
				return redirect("Ecommerce:RequestRefund")
			except ObjectDoesNotExist:
				print("ypo")
				messages.info(self.request, "this order dosent exist at all")
		return redirect("Ecommerce:RequestRefund")
			