;; Builds the open-source Racer reasoner with Clozure CL and saves it as a
;; standalone executable named RacerPro (the binary name that the DLVHEX
;; DL-Plugin expects to find). Lisp dependencies (aserve, etc.) come from
;; Quicklisp, as Racer's README instructs.
(load "/root/quicklisp/setup.lisp")
(pushnew #P"/opt/Racer/" asdf:*central-registry* :test #'equal)
(ql:register-local-projects)

;; racer.asd declares its dependencies as (:require "aserve") etc., i.e. raw
;; cl:require calls. We preload them via Quicklisp and register a module
;; provider that bridges require -> quickload. Racer's sources stay untouched.
(handler-case
    (ql:quickload '("aserve" "flexi-streams" "deflate"))
  (error (e)
    (format t "~%DEPS LOAD ERROR: ~a~%" e)
    (ccl:quit 1)))

(defun quicklisp-module-provider (module)
  (let ((name (string-downcase (string module))))
    (handler-case
        (progn (ql:quickload name :silent t)
               (provide module)
               t)
      (error () nil))))
(pushnew 'quicklisp-module-provider ccl:*module-provider-functions*)

(handler-case
    (ql:quickload "racer")
  (error (e)
    (format t "~%RACER LOAD ERROR: ~a~%" e)
    (ccl:quit 1)))

(format t "~%Racer loaded OK, installing dlvhex compatibility hook...~%")

;; The DLVHEX DL-Plugin was written against RacerPro 1.9, whose nRQL protocol
;; had a (state <assertion>*) operator for applying ABox changes in sequence.
;; Open-source Racer dropped it, but exposes the official extension point
;; thematic-substrate:*server-hooks* for unknown operators. This hook executes
;; each assertion inside (state ...) by calling the corresponding function in
;; the racer package (add-concept-assertion, etc.). No Racer sources modified.
(defun dlvhex-state-compat-hook (expr)
  (if (and (consp expr)
           (symbolp (first expr))
           (string-equal (symbol-name (first expr)) "STATE"))
      (progn
        (dolist (sub (rest expr))
          (when (and (consp sub) (symbolp (first sub)))
            (let ((fn (find-symbol (string-upcase (symbol-name (first sub)))
                                   (find-package :racer))))
              (when (and fn (fboundp fn))
                (apply fn (rest sub))))))
        :ok)
      :hook-not-found))

(thematic-substrate:server-hook 'dlvhex-state-compat-hook)

(format t "~%Hook installed, saving image...~%")

(ccl:save-application "/usr/local/bin/RacerPro"
                      :toplevel-function
                      (lambda ()
                        (funcall (find-symbol "RACER-TOPLEVEL" "RACER")))
                      :prepend-kernel t)
