#!/bin/bash

# Add cache clear after ButtonStrip create
sed -i '/ButtonStripType.objects.create(/,/serializer = ButtonStripTypeSerializer(button_strip, context.*$/{ /serializer = ButtonStripTypeSerializer(button_strip, context.*$/i\                    # Clear cache so new button strip appears immediately\n                    clear_fabric_cache()
}' views.py

# Add cache clear after ButtonStrip update
sed -i '/button_strip_type.save()/a\                        # Clear cache so updated button strip appears immediately\n                        clear_fabric_cache()' views.py

# Add cache clear after ButtonStrip delete
sed -i '/button_strip_type.delete()/a\                    # Clear cache so deleted button strip disappears immediately\n                    clear_fabric_cache()' views.py

# Add cache clear after Body create
sed -i '/BodyType.objects.create(/,/serializer = BodyTypeSerializer(body, context.*$/{ /serializer = BodyTypeSerializer(body, context.*$/i\                    # Clear cache so new body appears immediately\n                    clear_fabric_cache()
}' views.py

# Add cache clear after Body update
sed -i '/body_type.save()/a\                        # Clear cache so updated body appears immediately\n                        clear_fabric_cache()' views.py

# Add cache clear after Body delete
sed -i '/body_type.delete()/a\                    # Clear cache so deleted body disappears immediately\n                    clear_fabric_cache()' views.py

echo "✅ Cache clear calls added to all part types!"
