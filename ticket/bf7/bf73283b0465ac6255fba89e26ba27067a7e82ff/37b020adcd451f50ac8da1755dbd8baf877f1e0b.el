
(provide 'amp)


(defun amp-length-prefixed (str)
  (let* ((fulllen (string-bytes str))
         (byte2 (% fulllen 256))
         (byte1 (/ fulllen 256)))
    (concat (vector byte1 byte2) str)))

(defun amp-packet (alist)
  (let ((buf ""))
    (loop for item in alist do
          (let ((key (car item))
                (value (cdr item)))
            (setf buf (concat buf
                              (amp-length-prefixed (symbol-name key))
                              (amp-length-prefixed value)))))
    (concat buf [0 0])
    ))


(defstruct ampconn
  skt)


(defun connect-amp (host port)

  (lexical-let* ((skt (open-network-stream "amp" nil host port))
                 (parse-state 'FIRSTLEN)
                 (the-string "")
                 (the-packet '())
                 (string-length 0)
                 (string-state 'KEY)
                 (key "")
                 (string-received (lambda (s) ))
                 (result (make-ampconn)))
    (set-process-filter
     skt
     (lambda (proc data)
       ;; (message (format "DATA INCOMING: %s" (symbol-name (type-of data))))
       (loop for byte across data do
             (case parse-state
               ('FIRSTLEN
                (setf string-length (* 256 byte))
                (setf parse-state 'SECLEN))
               ('SECLEN
                (setf string-length (+ string-length byte))
                (if (eq string-length 0)
                    (progn
                      (message (format "PACKET: %s" the-packet))
                      ;; FULL METAL PACKET
                      (setf the-packet ()))
                  (setf parse-state 'STRDAT)))
               ('STRDAT
                (decf string-length)
                (setf the-string (concat the-string (vector byte)))
                (if (eq string-length 0)
                    (progn
                      ;; got a string!  deal with it!
                      (case string-state
                        ('KEY
                         (setf key the-string)
                         (setf string-state 'VALUE))
                        ('VALUE
                         (setf the-packet
                               (append the-packet
                                       (list (cons (intern key)
                                                   the-string))))
                                (setf string-state 'KEY)))
                      (message (format "GOT: %s" the-string))
                      ;; OK done dealing with it
                      (setf the-string "")
                      (setf parse-state 'FIRSTLEN))
                  ;; (funcall 'string-received the-string))
                  )
                ))
             )))
    (setf (ampconn-skt result) skt)
    result
    ))

(process-send-string
 (ampconn-skt ca)
 (amp-packet '((_ask . "lala")
               (_command . "Divide")
               (numerator . "25")
               (denominator . "0"))))

