// SPDX-License-Identifier: GPL-3.0-or-later

import { initialiseWordPressEmulators } from "./wordpress.ts";

/** This module is enqueued only on WordPress pages containing the shortcode. */
if (typeof document !== "undefined") {
  initialiseWordPressEmulators(document);
}
