from django.urls import path, include
from . import views
from .views import (
    FabricTypeAdminSideAPIView, FabricColorAdminSideAPIView,
    GholaTypeAdminSideAPIView,
    SleevesTypeAdminSideAPIView, PocketTypeAdminSideAPIView, ButtonTypeAdminSideAPIView,
    ButtonStripTypeAdminSideAPIView, BodyTypeAdminSideAPIView, MainCatogeryAdminSideAPIView, MainCatogeryUserSideAPIView,
    FetchFabricAPIView, FetchFabricDetailAPIView, FetchFabricColorsAPIView_New, FetchCollerAPIView, UserDesignAPIView, FetchSleevesRightAPIView,
    FetchSleevesLeftAPIView, FetchPocketAPIView, FetchButtonAPIView, FetchButtonStripAPIView, FetchBodyAPIView,
    CalculateDesignPriceAPIView, DesignSummaryPreviewAPIView,
    LowStockAlertAPIView, BulkUpdateInventoryAPIView, InventoryHistoryAPIView,
    UploadDesignScreenshotAPIView
)
urlpatterns = [
    path('', views.all_design_view, name='all-designs'),
    #============ MAIN CATEGORY END-USER SIDE =======================================
    path('fetch/main/category/', MainCatogeryUserSideAPIView.as_view()),
    #============ Fabric END-USER SIDE (NEW) =======================================
    path('fetch/fabric/', FetchFabricAPIView.as_view()),  # Fetch all FabricType
    path('fetch/fabric/<int:fabric_id>/', FetchFabricDetailAPIView.as_view()),  # Fetch single fabric details
    path('fetch/fabric/<int:fabric_id>/colors/', FetchFabricColorsAPIView_New.as_view()),  # Fetch colors for a fabric
    #============ Coller (Ghola) END-USER SIDE =======================================
    path('fetch/coller/', FetchCollerAPIView.as_view()),
        #============ Sleeves  END-USER SIDE =======================================
    path('fetch/sleeves/right/', FetchSleevesRightAPIView.as_view()),
    path('fetch/sleeves/left/', FetchSleevesLeftAPIView.as_view()),
    #============ Pocket END-USER SIDE =======================================
    path('fetch/pocket/', FetchPocketAPIView.as_view()),
    #============ Button END-USER SIDE =======================================
    path('fetch/button/', FetchButtonAPIView.as_view()),
    #============ Button Strip END-USER SIDE =======================================
    path('fetch/button-strip/', FetchButtonStripAPIView.as_view()),
    #============ Body END-USER SIDE =======================================
    path('fetch/body/', FetchBodyAPIView.as_view()),
    #============ Design END-USER SIDE =======================================
    path('fetch/designs/', UserDesignAPIView.as_view()),
    path('calculate-price/', CalculateDesignPriceAPIView.as_view()),
    path('preview/summary/', DesignSummaryPreviewAPIView.as_view()),
    path('create/design/', UserDesignAPIView.as_view()),
    path('edit/design/<int:pk>/', UserDesignAPIView.as_view()),
    path('upload/screenshot/', UploadDesignScreenshotAPIView.as_view()),
    #============ MAIN CATEGORY ADMIN SIDE =======================================
    path('detail/main/category/<int:pk>/', MainCatogeryAdminSideAPIView.as_view()),
    path('create/main/category/', MainCatogeryAdminSideAPIView.as_view()),
    path('update/main/category/<int:pk>/', MainCatogeryAdminSideAPIView.as_view()),
    path('delete/main/category/<int:pk>/', MainCatogeryAdminSideAPIView.as_view()),

    #============ NEW: FABRIC TYPE ADMIN SIDE =======================================
    
    # path("test/fabric-types/", views.all_fabric_types, name="all-fabric-types"),
    
    
    
    path('detail/fabric-type/<int:pk>/', FabricTypeAdminSideAPIView.as_view()),
    path('create/fabric-type/', FabricTypeAdminSideAPIView.as_view()),
    path('update/fabric-type/<int:pk>/', FabricTypeAdminSideAPIView.as_view()),
    path('delete/fabric-type/<int:pk>/', FabricTypeAdminSideAPIView.as_view()),

    #============ NEW: FABRIC COLOR ADMIN SIDE =======================================
    path('detail/fabric-color/<int:pk>/', FabricColorAdminSideAPIView.as_view()),
    path('create/fabric-color/', FabricColorAdminSideAPIView.as_view()),
    path('update/fabric-color/<int:pk>/', FabricColorAdminSideAPIView.as_view()),
    path('delete/fabric-color/<int:pk>/', FabricColorAdminSideAPIView.as_view()),
    #============ GHOLATYPE ADMIN SIDE =======================================
    path('detail/ghola/<int:pk>/', GholaTypeAdminSideAPIView.as_view()),
    path('create/ghola/', GholaTypeAdminSideAPIView.as_view()),
    path('update/ghola/<int:pk>/', GholaTypeAdminSideAPIView.as_view()),
    path('delete/ghola/<int:pk>/', GholaTypeAdminSideAPIView.as_view()),

    #============ SleevesTYPE ADMIN SIDE =======================================
    path('detail/sleeve/<int:pk>/', SleevesTypeAdminSideAPIView.as_view()),
    path('create/sleeve/', SleevesTypeAdminSideAPIView.as_view()),
    path('update/sleeve/<int:pk>/', SleevesTypeAdminSideAPIView.as_view()),
    path('delete/sleeve/<int:pk>/', SleevesTypeAdminSideAPIView.as_view()),

    #============ PocketTYPE ADMIN SIDE =======================================
    path('detail/pocket/<int:pk>/', PocketTypeAdminSideAPIView.as_view()),
    path('create/pocket/', PocketTypeAdminSideAPIView.as_view()),
    path('update/pocket/<int:pk>/', PocketTypeAdminSideAPIView.as_view()),
    path('delete/pocket/<int:pk>/', PocketTypeAdminSideAPIView.as_view()),

    #============ ButtonTYPE ADMIN SIDE =======================================
    path('detail/button/<int:pk>/', ButtonTypeAdminSideAPIView.as_view()),
    path('create/button/', ButtonTypeAdminSideAPIView.as_view()),
    path('update/button/<int:pk>/', ButtonTypeAdminSideAPIView.as_view()),
    path('delete/button/<int:pk>/', ButtonTypeAdminSideAPIView.as_view()),

    #============ ButtonStripTYPE ADMIN SIDE =======================================
    path('detail/button-strip/<int:pk>/', ButtonStripTypeAdminSideAPIView.as_view()),
    path('create/button-strip/', ButtonStripTypeAdminSideAPIView.as_view()),
    path('update/button-strip/<int:pk>/', ButtonStripTypeAdminSideAPIView.as_view()),
    path('delete/button-strip/<int:pk>/', ButtonStripTypeAdminSideAPIView.as_view()),

    #============ BodyTYPE ADMIN SIDE =======================================
    path('detail/body/<int:pk>/', BodyTypeAdminSideAPIView.as_view()),
    path('create/body/', BodyTypeAdminSideAPIView.as_view()),
    path('update/body/<int:pk>/', BodyTypeAdminSideAPIView.as_view()),
    path('delete/body/<int:pk>/', BodyTypeAdminSideAPIView.as_view()),

    #============ INVENTORY MANAGEMENT (ADMIN SIDE) =======================================
    path('inventory/low-stock/', LowStockAlertAPIView.as_view(), name='inventory-low-stock'),
    path('inventory/bulk-update/', BulkUpdateInventoryAPIView.as_view(), name='inventory-bulk-update'),
    path('inventory/history/<int:pk>/', InventoryHistoryAPIView.as_view(), name='inventory-history'),

]

app_name = 'Design-api'
