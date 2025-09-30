from django.contrib import admin
from .models import Resume, CustomUser, PendingPayment

# Action function to revoke credits for selected payments
@admin.action(description="Mark selected payments as Revoked and deduct credits")
def revoke_credits(modeladmin, request, queryset):
    for payment in queryset:
        if payment.status != 'revoked':
            # Deduct the credits that were given on trust
            user = payment.user
            user.credits -= payment.amount
            if user.credits < 0:
                user.credits = 0 # Ensure credits don't go negative
            user.save()
            
            # Update the payment status
            payment.status = 'revoked'
            payment.save()

# Action function to confirm payments
@admin.action(description="Mark selected payments as Confirmed")
def confirm_payment(modeladmin, request, queryset):
    queryset.update(status='confirmed')


class PendingPaymentAdmin(admin.ModelAdmin):
    # Fields to display in the main list view
    list_display = ('user', 'transaction_id', 'amount', 'status', 'created_at')
    
    # Allow filtering by status
    list_filter = ('status',)
    
    # Allow searching by user's email or transaction ID
    search_fields = ('user__email', 'transaction_id')
    
    # Make most fields read-only to prevent accidental changes
    readonly_fields = ('user', 'transaction_id', 'amount', 'created_at', 'updated_at')
    
    # Add the custom actions to the admin interface
    actions = [revoke_credits, confirm_payment]

    # Organize the detail view
    fieldsets = (
        (None, {
            'fields': ('user', 'transaction_id', 'amount', 'status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

class CustomUserAdmin(admin.ModelAdmin):
    # Display user's email, username, and credits in the user list
    list_display = ('email', 'username', 'credits', 'is_staff')
    search_fields = ('email', 'username')

    # Make credits editable in the admin panel
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login',)}),
        ('Credits', {'fields': ('credits',)}),
    )
    # Note: Password is not displayed for security, only changed.

# Register your models with the admin site
admin.site.register(Resume)
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(PendingPayment, PendingPaymentAdmin)