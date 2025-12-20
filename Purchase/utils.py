from decimal import Decimal
from Design.models import FabricColor, InventoryTransaction


def check_stock_availability(user_design):
    """
    Check if all components in the user design are in stock
    Returns: (is_available: bool, out_of_stock_items: list)
    """
    out_of_stock_items = []

    # Check main fabric color
    if user_design.main_body_fabric_color:
        fabric = user_design.main_body_fabric_color
        if not fabric.inStock or fabric.quantity < 1:
            out_of_stock_items.append({
                'component': 'Main Fabric',
                'name': fabric.color_name_eng,
                'available_quantity': fabric.quantity
            })

    # Check collar/ghola type fabric
    if user_design.selected_coller_type and user_design.selected_coller_type.fabric_color:
        fabric = user_design.selected_coller_type.fabric_color
        if not fabric.inStock or fabric.quantity < 1:
            out_of_stock_items.append({
                'component': 'Collar Fabric',
                'name': fabric.color_name_eng,
                'available_quantity': fabric.quantity
            })

    # Check left sleeve fabric
    if user_design.selected_sleeve_left_type and user_design.selected_sleeve_left_type.fabric_color:
        fabric = user_design.selected_sleeve_left_type.fabric_color
        if not fabric.inStock or fabric.quantity < 1:
            out_of_stock_items.append({
                'component': 'Left Sleeve Fabric',
                'name': fabric.color_name_eng,
                'available_quantity': fabric.quantity
            })

    # Check right sleeve fabric
    if user_design.selected_sleeve_right_type and user_design.selected_sleeve_right_type.fabric_color:
        fabric = user_design.selected_sleeve_right_type.fabric_color
        if not fabric.inStock or fabric.quantity < 1:
            out_of_stock_items.append({
                'component': 'Right Sleeve Fabric',
                'name': fabric.color_name_eng,
                'available_quantity': fabric.quantity
            })

    # Check pocket fabric
    if user_design.selected_pocket_type and user_design.selected_pocket_type.fabric_color:
        fabric = user_design.selected_pocket_type.fabric_color
        if not fabric.inStock or fabric.quantity < 1:
            out_of_stock_items.append({
                'component': 'Pocket Fabric',
                'name': fabric.color_name_eng,
                'available_quantity': fabric.quantity
            })

    # Check button fabric
    if user_design.selected_button_type and user_design.selected_button_type.fabric_color:
        fabric = user_design.selected_button_type.fabric_color
        if not fabric.inStock or fabric.quantity < 1:
            out_of_stock_items.append({
                'component': 'Button Fabric',
                'name': fabric.color_name_eng,
                'available_quantity': fabric.quantity
            })

    # Check button strip fabric
    if user_design.selected_button_strip_type and user_design.selected_button_strip_type.fabric_color:
        fabric = user_design.selected_button_strip_type.fabric_color
        if not fabric.inStock or fabric.quantity < 1:
            out_of_stock_items.append({
                'component': 'Button Strip Fabric',
                'name': fabric.color_name_eng,
                'available_quantity': fabric.quantity
            })

    is_available = len(out_of_stock_items) == 0
    return is_available, out_of_stock_items


def deduct_inventory(user_design, order_invoice_number=None):
    """
    Deduct inventory for all components in the user design
    This should be called within a transaction to ensure atomicity
    """
    fabric_colors_to_deduct = []

    # Collect all fabric colors used in the design
    if user_design.main_body_fabric_color:
        fabric_colors_to_deduct.append(user_design.main_body_fabric_color)

    if user_design.selected_coller_type and user_design.selected_coller_type.fabric_color:
        fabric_colors_to_deduct.append(user_design.selected_coller_type.fabric_color)

    if user_design.selected_sleeve_left_type and user_design.selected_sleeve_left_type.fabric_color:
        fabric_colors_to_deduct.append(user_design.selected_sleeve_left_type.fabric_color)

    if user_design.selected_sleeve_right_type and user_design.selected_sleeve_right_type.fabric_color:
        fabric_colors_to_deduct.append(user_design.selected_sleeve_right_type.fabric_color)

    if user_design.selected_pocket_type and user_design.selected_pocket_type.fabric_color:
        fabric_colors_to_deduct.append(user_design.selected_pocket_type.fabric_color)

    if user_design.selected_button_type and user_design.selected_button_type.fabric_color:
        fabric_colors_to_deduct.append(user_design.selected_button_type.fabric_color)

    if user_design.selected_button_strip_type and user_design.selected_button_strip_type.fabric_color:
        fabric_colors_to_deduct.append(user_design.selected_button_strip_type.fabric_color)

    # Deduct inventory for each unique fabric color
    deducted_fabrics = set()  # Track unique fabrics to avoid double deduction
    for fabric_color in fabric_colors_to_deduct:
        if fabric_color.id not in deducted_fabrics:
            if fabric_color.quantity > 0:
                quantity_before = fabric_color.quantity
                fabric_color.quantity -= 1
                quantity_after = fabric_color.quantity
                fabric_color.save()
                deducted_fabrics.add(fabric_color.id)

                # Log transaction
                InventoryTransaction.objects.create(
                    fabric_color=fabric_color,
                    transaction_type='ORDER',
                    quantity_change=-1,
                    quantity_before=quantity_before,
                    quantity_after=quantity_after,
                    reference_order=order_invoice_number,
                    notes=f"Deducted for design #{user_design.id}"
                )

                # Update inStock status if quantity reaches 0
                if fabric_color.quantity == 0:
                    fabric_color.inStock = False
                    fabric_color.save()


def restore_inventory(user_design, order_invoice_number=None):
    """
    Restore inventory when an order is cancelled
    This should be called within a transaction to ensure atomicity
    """
    fabric_colors_to_restore = []

    # Collect all fabric colors used in the design
    if user_design.main_body_fabric_color:
        fabric_colors_to_restore.append(user_design.main_body_fabric_color)

    if user_design.selected_coller_type and user_design.selected_coller_type.fabric_color:
        fabric_colors_to_restore.append(user_design.selected_coller_type.fabric_color)

    if user_design.selected_sleeve_left_type and user_design.selected_sleeve_left_type.fabric_color:
        fabric_colors_to_restore.append(user_design.selected_sleeve_left_type.fabric_color)

    if user_design.selected_sleeve_right_type and user_design.selected_sleeve_right_type.fabric_color:
        fabric_colors_to_restore.append(user_design.selected_sleeve_right_type.fabric_color)

    if user_design.selected_pocket_type and user_design.selected_pocket_type.fabric_color:
        fabric_colors_to_restore.append(user_design.selected_pocket_type.fabric_color)

    if user_design.selected_button_type and user_design.selected_button_type.fabric_color:
        fabric_colors_to_restore.append(user_design.selected_button_type.fabric_color)

    if user_design.selected_button_strip_type and user_design.selected_button_strip_type.fabric_color:
        fabric_colors_to_restore.append(user_design.selected_button_strip_type.fabric_color)

    # Restore inventory for each unique fabric color
    restored_fabrics = set()  # Track unique fabrics to avoid double restoration
    for fabric_color in fabric_colors_to_restore:
        if fabric_color.id not in restored_fabrics:
            quantity_before = fabric_color.quantity
            fabric_color.quantity += 1
            quantity_after = fabric_color.quantity
            fabric_color.inStock = True  # Mark as in stock
            fabric_color.save()
            restored_fabrics.add(fabric_color.id)

            # Log transaction
            InventoryTransaction.objects.create(
                fabric_color=fabric_color,
                transaction_type='CANCEL',
                quantity_change=1,
                quantity_before=quantity_before,
                quantity_after=quantity_after,
                reference_order=order_invoice_number,
                notes=f"Restored after order cancellation for design #{user_design.id}"
            )


def calculate_basket_total(basket_items):
    """
    Calculate total price from basket items
    """
    total = Decimal('0.000')
    for item in basket_items:
        total += item.subTotal
    return total
